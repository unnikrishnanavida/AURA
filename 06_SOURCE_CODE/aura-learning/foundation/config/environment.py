from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import re
import threading
import time

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PREFIX = "AURA_"
DEFAULT_SEPARATOR = "_"
DEFAULT_DOTENV_ENCODING = "utf-8"
DEFAULT_MAX_HISTORY = 1000

TRUE_VALUES = frozenset({
    "1", "true", "yes", "y", "on", "enabled", "enable",
    "t", "ok",
})

FALSE_VALUES = frozenset({
    "0", "false", "no", "n", "off", "disabled", "disable",
    "f",
})

NULL_VALUES = frozenset({
    "", "null", "none", "~",
})

SENSITIVE_NAME_PARTS = frozenset({
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
    "credentials",
    "authorization",
    "auth",
    "session",
    "cookie",
})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class EnvironmentErrorBase(Exception):
    """Base exception for environment configuration errors."""


class EnvironmentKeyError(EnvironmentErrorBase, KeyError):
    """Raised when an environment key is required but missing."""


class EnvironmentParseError(EnvironmentErrorBase, ValueError):
    """Raised when an environment value cannot be parsed."""


class EnvironmentValidationError(EnvironmentErrorBase, ValueError):
    """Raised when an environment value fails validation."""


class EnvironmentMutationError(EnvironmentErrorBase):
    """Raised when the process environment cannot be modified."""


class DotenvParseError(EnvironmentErrorBase, ValueError):
    """Raised for malformed .env content."""


class EnvironmentFrozenError(EnvironmentErrorBase):
    """Raised when mutation is attempted on a frozen environment."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EnvironmentValueType(StrEnum):
    """Supported conversion types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    JSON = "json"
    LIST = "list"
    SET = "set"
    TUPLE = "tuple"
    OPTIONAL = "optional"
    NULL = "null"


class EnvironmentChangeType(StrEnum):
    """Types of environment mutations."""

    SET = "set"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    CLEAR = "clear"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnvironmentSpec:
    """Specification describing one supported environment variable."""

    name: str
    value_type: EnvironmentValueType = EnvironmentValueType.STRING
    required: bool = False
    default: Any = None
    description: str = ""
    secret: bool = False
    nullable: bool = True
    choices: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    aliases: tuple[str, ...] = ()
    delimiter: str = ","

    def normalized(self) -> "EnvironmentSpec":
        return EnvironmentSpec(
            name=normalize_env_name(self.name),
            value_type=self.value_type,
            required=self.required,
            default=self.default,
            description=self.description,
            secret=self.secret,
            nullable=self.nullable,
            choices=tuple(self.choices),
            minimum=self.minimum,
            maximum=self.maximum,
            aliases=tuple(
                normalize_env_name(alias)
                for alias in self.aliases
            ),
            delimiter=self.delimiter,
        )


@dataclass(frozen=True)
class EnvironmentValue:
    """Typed value returned from an environment lookup."""

    name: str
    raw: str | None
    value: Any
    source: str
    value_type: EnvironmentValueType
    secret: bool = False

    def display_value(self) -> Any:
        if self.secret:
            return "***"
        return self.value

    def as_dict(
        self,
        *,
        reveal_secrets: bool = False,
    ) -> dict[str, Any]:
        return {
            "name": self.name,
            "raw": (
                self.raw
                if reveal_secrets or not self.secret
                else "***"
            ),
            "value": (
                copy.deepcopy(self.value)
                if reveal_secrets or not self.secret
                else "***"
            ),
            "source": self.source,
            "value_type": self.value_type.value,
            "secret": self.secret,
        }


@dataclass(frozen=True)
class EnvironmentChange:
    """Record of a single environment mutation."""

    name: str
    change_type: EnvironmentChangeType
    old_value: str | None
    new_value: str | None
    timestamp: float
    source: str = "runtime"

    def as_dict(
        self,
        *,
        reveal_values: bool = False,
        secret: bool = False,
    ) -> dict[str, Any]:
        if secret and not reveal_values:
            old_value = "***" if self.old_value is not None else None
            new_value = "***" if self.new_value is not None else None
        else:
            old_value = self.old_value
            new_value = self.new_value

        return {
            "name": self.name,
            "change_type": self.change_type.value,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Immutable snapshot of selected environment state."""

    values: Mapping[str, str]
    timestamp: float = field(default_factory=time.time)
    prefix: str = ""
    digest: str = ""

    def __post_init__(self) -> None:
        if not self.digest:
            object.__setattr__(
                self,
                "digest",
                environment_digest(self.values),
            )

    def get(
        self,
        name: str,
        default: str | None = None,
    ) -> str | None:
        return self.values.get(
            normalize_env_name(name),
            default,
        )

    def contains(
        self,
        name: str,
    ) -> bool:
        return normalize_env_name(name) in self.values

    def as_dict(self) -> dict[str, str]:
        return dict(self.values)


@dataclass(frozen=True)
class EnvironmentDiff:
    """Difference between two environment snapshots."""

    added: Mapping[str, str]
    removed: Mapping[str, str]
    changed: Mapping[str, tuple[str, str]]

    @property
    def is_empty(self) -> bool:
        return not (
            self.added
            or self.removed
            or self.changed
        )

    @property
    def changed_names(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                set(self.added)
                | set(self.removed)
                | set(self.changed)
            )
        )

    def as_dict(
        self,
        *,
        reveal_values: bool = True,
    ) -> dict[str, Any]:
        if reveal_values:
            return {
                "added": dict(self.added),
                "removed": dict(self.removed),
                "changed": {
                    key: list(values)
                    for key, values in self.changed.items()
                },
            }

        return {
            "added": {
                key: "***"
                for key in self.added
            },
            "removed": {
                key: "***"
                for key in self.removed
            },
            "changed": {
                key: ("***", "***")
                for key in self.changed
            },
        }


@dataclass(frozen=True)
class EnvironmentValidationResult:
    """Structured result returned by environment validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    checked: int = 0

    def raise_for_errors(self) -> None:
        if not self.valid:
            raise EnvironmentValidationError(
                "; ".join(self.errors)
            )


# ---------------------------------------------------------------------------
# Normalization and parsing helpers
# ---------------------------------------------------------------------------

def normalize_env_name(name: str) -> str:
    """Normalize a process environment variable name."""
    value = str(name).strip()

    if not value:
        raise EnvironmentKeyError(
            "Environment variable name cannot be empty."
        )

    value = value.replace("-", "_")
    value = value.replace(".", "_")
    value = re.sub(
        r"[^A-Za-z0-9_]",
        "_",
        value,
    )

    return value.upper()


def normalize_prefix(prefix: str) -> str:
    """Normalize an environment prefix."""
    value = str(prefix or "").strip()

    if not value:
        return ""

    value = normalize_env_name(value)

    if not value.endswith("_"):
        value += "_"

    return value


def environment_name(
    name: str,
    *,
    prefix: str = DEFAULT_PREFIX,
) -> str:
    """Build a normalized prefixed environment variable name."""
    return (
        normalize_prefix(prefix)
        + normalize_env_name(name)
    )


def is_sensitive_name(name: str) -> bool:
    """Return whether a name strongly suggests secret data."""
    normalized = normalize_env_name(name)
    parts = set(
        part.lower()
        for part in normalized.split("_")
        if part
    )

    return bool(
        parts & SENSITIVE_NAME_PARTS
    )


def mask_secret(
    value: Any,
    *,
    replacement: str = "***",
) -> str:
    """Mask a secret value for logs and diagnostics."""
    if value is None:
        return replacement

    return replacement


def environment_digest(
    values: Mapping[str, str],
) -> str:
    """Create a deterministic SHA-256 digest of environment values."""
    payload = "\n".join(
        f"{key}={values[key]}"
        for key in sorted(values)
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def parse_bool(
    value: Any,
) -> bool:
    """Parse common textual boolean representations."""
    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    text = str(value).strip().lower()

    if text in TRUE_VALUES:
        return True

    if text in FALSE_VALUES:
        return False

    raise EnvironmentParseError(
        f"Invalid boolean value: {value!r}"
    )


def parse_int(
    value: Any,
) -> int:
    """Parse an integer environment value."""
    try:
        return int(
            str(value).strip()
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise EnvironmentParseError(
            f"Invalid integer value: {value!r}"
        ) from exc


def parse_float(
    value: Any,
) -> float:
    """Parse a floating-point environment value."""
    try:
        return float(
            str(value).strip()
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise EnvironmentParseError(
            f"Invalid float value: {value!r}"
        ) from exc


def parse_json(
    value: Any,
) -> Any:
    """Parse JSON from an environment string."""
    if not isinstance(
        value,
        str,
    ):
        return value

    try:
        return json.loads(
            value
        )
    except json.JSONDecodeError as exc:
        raise EnvironmentParseError(
            f"Invalid JSON environment value: {value!r}"
        ) from exc


def parse_path(
    value: Any,
) -> Path:
    """Parse a filesystem path."""
    try:
        return Path(
            str(value)
        ).expanduser()
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise EnvironmentParseError(
            f"Invalid path value: {value!r}"
        ) from exc


def parse_list(
    value: Any,
    *,
    delimiter: str = ",",
) -> list[str]:
    """Parse a delimited environment list."""
    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            str(item)
            for item in value
        ]

    if value is None:
        return []

    return [
        item.strip()
        for item in str(value).split(
            delimiter
        )
        if item.strip()
    ]


def parse_set(
    value: Any,
    *,
    delimiter: str = ",",
) -> set[str]:
    """Parse a delimited environment set."""
    return set(
        parse_list(
            value,
            delimiter=delimiter,
        )
    )


def parse_typed(
    value: Any,
    value_type: EnvironmentValueType,
    *,
    delimiter: str = ",",
) -> Any:
    """Convert a raw value according to a declared type."""
    if value is None:
        return None

    if isinstance(
        value_type,
        str,
    ):
        value_type = EnvironmentValueType(
            value_type.lower()
        )

    if value_type == EnvironmentValueType.STRING:
        return str(value)

    if value_type == EnvironmentValueType.INTEGER:
        return parse_int(value)

    if value_type == EnvironmentValueType.FLOAT:
        return parse_float(value)

    if value_type == EnvironmentValueType.BOOLEAN:
        return parse_bool(value)

    if value_type == EnvironmentValueType.PATH:
        return parse_path(value)

    if value_type == EnvironmentValueType.JSON:
        return parse_json(value)

    if value_type == EnvironmentValueType.LIST:
        return parse_list(
            value,
            delimiter=delimiter,
        )

    if value_type == EnvironmentValueType.SET:
        return parse_set(
            value,
            delimiter=delimiter,
        )

    if value_type == EnvironmentValueType.TUPLE:
        return tuple(
            parse_list(
                value,
                delimiter=delimiter,
            )
        )

    if value_type == EnvironmentValueType.NULL:
        if (
            str(value).strip().lower()
            in NULL_VALUES
        ):
            return None

        raise EnvironmentParseError(
            f"Value {value!r} is not a null value."
        )

    if value_type == EnvironmentValueType.OPTIONAL:
        text = str(value).strip()

        if text.lower() in NULL_VALUES:
            return None

        return text

    raise EnvironmentParseError(
        f"Unsupported environment value type: "
        f"{value_type!r}"
    )


def serialize_typed(
    value: Any,
    value_type: EnvironmentValueType,
    *,
    delimiter: str = ",",
) -> str:
    """Convert a typed value to a process-environment string."""
    if value is None:
        return ""

    if value_type == EnvironmentValueType.BOOLEAN:
        return "true" if bool(value) else "false"

    if value_type == EnvironmentValueType.JSON:
        return json.dumps(
            value,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    if value_type in (
        EnvironmentValueType.LIST,
        EnvironmentValueType.TUPLE,
        EnvironmentValueType.SET,
    ):
        return delimiter.join(
            str(item)
            for item in value
        )

    if value_type == EnvironmentValueType.PATH:
        return str(value)

    return str(value)


# ---------------------------------------------------------------------------
# .env parsing
# ---------------------------------------------------------------------------

def strip_inline_comment(
    value: str,
) -> str:
    """Remove an unquoted inline # comment."""
    quote: str | None = None
    escaped = False

    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue

        if char == "#" and quote is None:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()

    return value.rstrip()


def unquote_value(
    value: str,
) -> str:
    """Remove matching single or double quotes."""
    text = value.strip()

    if len(text) < 2:
        return text

    if text[0] == text[-1] and text[0] in {"'", '"'}:
        inner = text[1:-1]

        if text[0] == '"':
            try:
                return bytes(
                    inner,
                    "utf-8",
                ).decode(
                    "unicode_escape"
                )
            except UnicodeDecodeError:
                return inner

        return inner.replace(
            "\'",
            "'",
        )

    return text


def parse_dotenv_line(
    line: str,
    *,
    line_number: int = 0,
) -> tuple[str, str] | None:
    """Parse one .env line."""
    stripped = line.strip()

    if not stripped:
        return None

    if stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped[7:].lstrip()

    if "=" not in stripped:
        raise DotenvParseError(
            f"Malformed .env line {line_number}: "
            f"{line!r}"
        )

    name, value = stripped.split(
        "=",
        1,
    )

    normalized = normalize_env_name(
        name
    )

    value = strip_inline_comment(
        value
    )

    return (
        normalized,
        unquote_value(value),
    )


def parse_dotenv(
    text: str,
) -> dict[str, str]:
    """Parse dotenv text into normalized variables."""
    result: dict[str, str] = {}

    for number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        parsed = parse_dotenv_line(
            line,
            line_number=number,
        )

        if parsed is None:
            continue

        name, value = parsed
        result[name] = value

    return result


def load_dotenv_file(
    path: str | Path,
    *,
    encoding: str = DEFAULT_DOTENV_ENCODING,
) -> dict[str, str]:
    """Load and parse a dotenv file."""
    file_path = Path(path)

    if not file_path.exists():
        raise DotenvParseError(
            f".env file does not exist: "
            f"{file_path}"
        )

    try:
        text = file_path.read_text(
            encoding=encoding
        )
    except OSError as exc:
        raise DotenvParseError(
            f"Unable to read .env file: "
            f"{file_path}"
        ) from exc

    return parse_dotenv(
        text
    )


def quote_dotenv_value(
    value: Any,
) -> str:
    """Serialize a value safely for a dotenv file."""
    text = str(value)

    if (
        not text
        or text != text.strip()
        or any(
            char in text
            for char in (
                "#",
                "=",
                "\n",
                "\r",
            )
        )
    ):
        escaped = (
            text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

        return f'"{escaped}"'

    return text


def dump_dotenv(
    values: Mapping[str, Any],
    *,
    include_header: bool = True,
) -> str:
    """Serialize values to dotenv format."""
    lines: list[str] = []

    if include_header:
        lines.extend([
            "# Generated by AURA.",
            "# Review secret values before committing this file.",
            "",
        ])

    for name in sorted(values):
        normalized = normalize_env_name(name)
        lines.append(
            f"{normalized}="
            f"{quote_dotenv_value(values[name])}"
        )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Environment store
# ---------------------------------------------------------------------------

class EnvironmentStore:
    """
    Thread-safe environment abstraction.

    The store can either wrap os.environ directly or use an isolated
    mutable mapping, which makes testing and staged configuration safe.
    """

    def __init__(
        self,
        environ: MutableMapping[str, str] | None = None,
        *,
        prefix: str = DEFAULT_PREFIX,
        separator: str = DEFAULT_SEPARATOR,
        max_history: int = DEFAULT_MAX_HISTORY,
        mutate_process: bool = True,
    ) -> None:
        self._environ = (
            environ
            if environ is not None
            else os.environ
        )
        self._prefix = normalize_prefix(
            prefix
        )
        self._separator = separator
        self._max_history = max(
            0,
            int(max_history),
        )
        self._mutate_process = bool(
            mutate_process
        )

        self._lock = threading.RLock()
        self._specs: dict[
            str,
            EnvironmentSpec,
        ] = {}
        self._aliases: dict[
            str,
            str,
        ] = {}
        self._history: list[
            EnvironmentChange
        ] = []
        self._listeners: list[
            Callable[
                [EnvironmentChange],
                None,
            ]
        ] = []
        self._frozen = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def separator(self) -> str:
        return self._separator

    @property
    def frozen(self) -> bool:
        with self._lock:
            return self._frozen

    @property
    def mutate_process(self) -> bool:
        return self._mutate_process

    # ------------------------------------------------------------------
    # Name handling
    # ------------------------------------------------------------------

    def normalize(
        self,
        name: str,
    ) -> str:
        return normalize_env_name(
            name
        )

    def prefixed(
        self,
        name: str,
    ) -> str:
        return environment_name(
            name,
            prefix=self._prefix,
        )

    def resolve_alias(
        self,
        name: str,
    ) -> str:
        normalized = self.normalize(
            name
        )

        with self._lock:
            return self._aliases.get(
                normalized,
                normalized,
            )

    # ------------------------------------------------------------------
    # Specifications
    # ------------------------------------------------------------------

    def register_spec(
        self,
        spec: EnvironmentSpec,
        *,
        replace: bool = False,
    ) -> EnvironmentSpec:
        if not isinstance(
            spec,
            EnvironmentSpec,
        ):
            raise TypeError(
                "spec must be EnvironmentSpec."
            )

        normalized = spec.normalized()

        with self._lock:
            if (
                normalized.name in self._specs
                and not replace
            ):
                raise EnvironmentValidationError(
                    f"Environment spec '{normalized.name}' "
                    "already exists."
                )

            self._specs[
                normalized.name
            ] = normalized

            for alias in normalized.aliases:
                self._aliases[
                    alias
                ] = normalized.name

        return normalized

    def register_specs(
        self,
        specs: Iterable[EnvironmentSpec],
        *,
        replace: bool = False,
    ) -> list[EnvironmentSpec]:
        return [
            self.register_spec(
                spec,
                replace=replace,
            )
            for spec in specs
        ]

    def unregister_spec(
        self,
        name: str,
    ) -> EnvironmentSpec | None:
        normalized = self.resolve_alias(
            name
        )

        with self._lock:
            spec = self._specs.pop(
                normalized,
                None,
            )

            aliases = [
                alias
                for alias, target
                in self._aliases.items()
                if target == normalized
            ]

            for alias in aliases:
                self._aliases.pop(
                    alias,
                    None,
                )

            return spec

    def get_spec(
        self,
        name: str,
    ) -> EnvironmentSpec | None:
        normalized = self.resolve_alias(
            name
        )

        with self._lock:
            return self._specs.get(
                normalized
            )

    def specs(self) -> list[EnvironmentSpec]:
        with self._lock:
            return list(
                self._specs.values()
            )

    # ------------------------------------------------------------------
    # Raw access
    # ------------------------------------------------------------------

    def raw_get(
        self,
        name: str,
        default: str | None = None,
    ) -> str | None:
        normalized = self.resolve_alias(
            name
        )

        with self._lock:
            return self._environ.get(
                normalized,
                default,
            )

    def raw_contains(
        self,
        name: str,
    ) -> bool:
        normalized = self.resolve_alias(
            name
        )

        with self._lock:
            return normalized in self._environ

    def raw_set(
        self,
        name: str,
        value: Any,
        *,
        source: str = "runtime",
        allow_empty: bool = True,
    ) -> None:
        self._ensure_mutable()

        normalized = self.resolve_alias(
            name
        )

        if value is None:
            if allow_empty:
                text = ""
            else:
                raise EnvironmentMutationError(
                    f"Environment value for '{normalized}' "
                    "cannot be None."
                )
        else:
            text = str(value)

        with self._lock:
            old = self._environ.get(
                normalized
            )

            if self._mutate_process:
                self._environ[
                    normalized
                ] = text
            else:
                self._environ[
                    normalized
                ] = text

        self._record_change(
            EnvironmentChange(
                name=normalized,
                change_type=(
                    EnvironmentChangeType.UPDATE
                    if old is not None
                    else EnvironmentChangeType.SET
                ),
                old_value=old,
                new_value=text,
                timestamp=time.time(),
                source=source,
            )
        )

    def raw_delete(
        self,
        name: str,
        *,
        source: str = "runtime",
    ) -> bool:
        self._ensure_mutable()

        normalized = self.resolve_alias(
            name
        )

        with self._lock:
            if normalized not in self._environ:
                return False

            old = self._environ.pop(
                normalized
            )

        self._record_change(
            EnvironmentChange(
                name=normalized,
                change_type=EnvironmentChangeType.DELETE,
                old_value=old,
                new_value=None,
                timestamp=time.time(),
                source=source,
            )
        )

        return True

    # ------------------------------------------------------------------
    # Typed access
    # ------------------------------------------------------------------

    def get(
        self,
        name: str,
        default: Any = None,
        *,
        value_type: EnvironmentValueType | None = None,
        required: bool | None = None,
        nullable: bool | None = None,
        delimiter: str | None = None,
    ) -> Any:
        normalized = self.resolve_alias(
            name
        )

        spec = self.get_spec(
            normalized
        )

        if value_type is None and spec is not None:
            value_type = spec.value_type

        if required is None:
            required = (
                spec.required
                if spec is not None
                else False
            )

        if nullable is None:
            nullable = (
                spec.nullable
                if spec is not None
                else True
            )

        if delimiter is None:
            delimiter = (
                spec.delimiter
                if spec is not None
                else self._separator
            )

        raw = self.raw_get(
            normalized
        )

        if raw is None:
            if spec is not None:
                if spec.default is not None:
                    return copy.deepcopy(
                        spec.default
                    )

            if required:
                raise EnvironmentKeyError(
                    f"Required environment variable "
                    f"'{normalized}' is missing."
                )

            return default

        if (
            not raw
            and nullable
            and value_type
            in {
                EnvironmentValueType.OPTIONAL,
                EnvironmentValueType.NULL,
            }
        ):
            return None

        if value_type is None:
            value_type = EnvironmentValueType.STRING

        return parse_typed(
            raw,
            value_type,
            delimiter=delimiter,
        )

    def require(
        self,
        name: str,
        *,
        value_type: EnvironmentValueType | None = None,
    ) -> Any:
        return self.get(
            name,
            value_type=value_type,
            required=True,
        )

    def get_value(
        self,
        name: str,
        *,
        value_type: EnvironmentValueType | None = None,
    ) -> EnvironmentValue:
        normalized = self.resolve_alias(
            name
        )

        spec = self.get_spec(
            normalized
        )

        selected_type = (
            value_type
            or (
                spec.value_type
                if spec is not None
                else EnvironmentValueType.STRING
            )
        )

        raw = self.raw_get(
            normalized
        )

        value = self.get(
            normalized,
            value_type=selected_type,
        )

        return EnvironmentValue(
            name=normalized,
            raw=raw,
            value=value,
            source=(
                "environment"
                if raw is not None
                else "default"
            ),
            value_type=selected_type,
            secret=(
                spec.secret
                if spec is not None
                else is_sensitive_name(normalized)
            ),
        )

    # ------------------------------------------------------------------
    # Typed convenience methods
    # ------------------------------------------------------------------

    def get_string(
        self,
        name: str,
        default: str | None = None,
        *,
        required: bool = False,
    ) -> str | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.STRING,
            required=required,
        )

        if value is None:
            return None

        return str(value)

    def get_int(
        self,
        name: str,
        default: int | None = None,
        *,
        required: bool = False,
    ) -> int | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.INTEGER,
            required=required,
        )

        if value is None:
            return None

        return int(value)

    def get_float(
        self,
        name: str,
        default: float | None = None,
        *,
        required: bool = False,
    ) -> float | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.FLOAT,
            required=required,
        )

        if value is None:
            return None

        return float(value)

    def get_bool(
        self,
        name: str,
        default: bool | None = None,
        *,
        required: bool = False,
    ) -> bool | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.BOOLEAN,
            required=required,
        )

        if value is None:
            return None

        return bool(value)

    def get_path(
        self,
        name: str,
        default: str | Path | None = None,
        *,
        required: bool = False,
    ) -> Path | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.PATH,
            required=required,
        )

        if value is None:
            return None

        return Path(value)

    def get_json(
        self,
        name: str,
        default: Any = None,
        *,
        required: bool = False,
    ) -> Any:
        return self.get(
            name,
            default,
            value_type=EnvironmentValueType.JSON,
            required=required,
        )

    def get_list(
        self,
        name: str,
        default: Sequence[str] | None = None,
        *,
        delimiter: str = ",",
        required: bool = False,
    ) -> list[str] | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.LIST,
            required=required,
            delimiter=delimiter,
        )

        if value is None:
            return None

        return list(value)

    def get_set(
        self,
        name: str,
        default: Iterable[str] | None = None,
        *,
        delimiter: str = ",",
        required: bool = False,
    ) -> set[str] | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.SET,
            required=required,
            delimiter=delimiter,
        )

        if value is None:
            return None

        return set(value)

    def get_tuple(
        self,
        name: str,
        default: Sequence[str] | None = None,
        *,
        delimiter: str = ",",
        required: bool = False,
    ) -> tuple[str, ...] | None:
        value = self.get(
            name,
            default,
            value_type=EnvironmentValueType.TUPLE,
            required=required,
            delimiter=delimiter,
        )

        if value is None:
            return None

        return tuple(value)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def set(
        self,
        name: str,
        value: Any,
        *,
        value_type: EnvironmentValueType | None = None,
        source: str = "runtime",
        validate: bool = True,
    ) -> None:
        self._ensure_mutable()

        normalized = self.resolve_alias(
            name
        )

        spec = self.get_spec(
            normalized
        )

        selected_type = (
            value_type
            or (
                spec.value_type
                if spec is not None
                else EnvironmentValueType.STRING
            )
        )

        if validate:
            self.validate_value(
                normalized,
                value,
            )

        text = serialize_typed(
            value,
            selected_type,
            delimiter=(
                spec.delimiter
                if spec is not None
                else self._separator
            ),
        )

        self.raw_set(
            normalized,
            text,
            source=source,
        )

    def set_many(
        self,
        values: Mapping[str, Any],
        *,
        source: str = "runtime",
        validate: bool = True,
    ) -> None:
        for name, value in values.items():
            self.set(
                name,
                value,
                source=source,
                validate=validate,
            )

    def delete(
        self,
        name: str,
        *,
        source: str = "runtime",
    ) -> bool:
        return self.raw_delete(
            name,
            source=source,
        )

    def clear(
        self,
        *,
        prefix: str | None = None,
        source: str = "runtime",
    ) -> int:
        self._ensure_mutable()

        names = self.names(
            prefix=prefix
        )

        removed = 0

        for name in names:
            if self.delete(
                name,
                source=source,
            ):
                removed += 1

        return removed

    # ------------------------------------------------------------------
    # Bulk inspection
    # ------------------------------------------------------------------

    def names(
        self,
        *,
        prefix: str | None = None,
    ) -> list[str]:
        selected_prefix = (
            normalize_prefix(prefix)
            if prefix is not None
            else self._prefix
        )

        with self._lock:
            names = [
                name
                for name in self._environ
                if (
                    not selected_prefix
                    or name.startswith(
                        selected_prefix
                    )
                )
            ]

        return sorted(
            names
        )

    def items(
        self,
        *,
        prefix: str | None = None,
        reveal_secrets: bool = True,
    ) -> list[tuple[str, str]]:
        result = []

        for name in self.names(
            prefix=prefix
        ):
            value = self.raw_get(
                name
            )

            if (
                not reveal_secrets
                and is_sensitive_name(name)
            ):
                value = "***"

            result.append(
                (
                    name,
                    "" if value is None else value,
                )
            )

        return result

    def to_dict(
        self,
        *,
        prefix: str | None = None,
        reveal_secrets: bool = False,
    ) -> dict[str, str]:
        return dict(
            self.items(
                prefix=prefix,
                reveal_secrets=reveal_secrets,
            )
        )

    def snapshot(
        self,
        *,
        prefix: str | None = None,
    ) -> EnvironmentSnapshot:
        values = self.to_dict(
            prefix=prefix,
            reveal_secrets=True,
        )

        return EnvironmentSnapshot(
            values=values,
            prefix=(
                normalize_prefix(prefix)
                if prefix is not None
                else self._prefix
            ),
        )

    # ------------------------------------------------------------------
    # Diff and restore
    # ------------------------------------------------------------------

    @staticmethod
    def diff(
        before: EnvironmentSnapshot,
        after: EnvironmentSnapshot,
    ) -> EnvironmentDiff:
        before_values = dict(
            before.values
        )
        after_values = dict(
            after.values
        )

        added = {
            key: after_values[key]
            for key in after_values.keys()
            - before_values.keys()
        }

        removed = {
            key: before_values[key]
            for key in before_values.keys()
            - after_values.keys()
        }

        changed = {
            key: (
                before_values[key],
                after_values[key],
            )
            for key in before_values.keys()
            & after_values.keys()
            if before_values[key]
            != after_values[key]
        }

        return EnvironmentDiff(
            added=added,
            removed=removed,
            changed=changed,
        )

    def restore(
        self,
        snapshot: EnvironmentSnapshot,
        *,
        prefix: str | None = None,
        source: str = "restore",
    ) -> EnvironmentDiff:
        self._ensure_mutable()

        current = self.snapshot(
            prefix=prefix
        )

        target = snapshot

        current_names = set(
            current.values
        )
        target_names = set(
            target.values
        )

        for name in current_names - target_names:
            self.delete(
                name,
                source=source,
            )

        for name, value in target.values.items():
            self.raw_set(
                name,
                value,
                source=source,
            )

        return self.diff(
            current,
            self.snapshot(
                prefix=prefix
            ),
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_value(
        self,
        name: str,
        value: Any,
    ) -> None:
        normalized = self.resolve_alias(
            name
        )

        spec = self.get_spec(
            normalized
        )

        if spec is None:
            return

        if value is None:
            if spec.nullable:
                return

            raise EnvironmentValidationError(
                f"'{normalized}' cannot be null."
            )

        if spec.choices and value not in spec.choices:
            raise EnvironmentValidationError(
                f"'{normalized}' must be one of "
                f"{spec.choices!r}."
            )

        if (
            spec.minimum is not None
            and isinstance(
                value,
                (int, float),
            )
            and value < spec.minimum
        ):
            raise EnvironmentValidationError(
                f"'{normalized}' cannot be less than "
                f"{spec.minimum}."
            )

        if (
            spec.maximum is not None
            and isinstance(
                value,
                (int, float),
            )
            and value > spec.maximum
        ):
            raise EnvironmentValidationError(
                f"'{normalized}' cannot exceed "
                f"{spec.maximum}."
            )

        parse_typed(
            serialize_typed(
                value,
                spec.value_type,
                delimiter=spec.delimiter,
            ),
            spec.value_type,
            delimiter=spec.delimiter,
        )

    def validate(
        self,
        *,
        strict_required: bool = True,
    ) -> EnvironmentValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        checked = 0

        for spec in self.specs():
            checked += 1
            raw = self.raw_get(
                spec.name
            )

            if raw is None:
                if (
                    spec.required
                    and strict_required
                    and spec.default is None
                ):
                    errors.append(
                        f"Required variable "
                        f"'{spec.name}' is missing."
                    )

                continue

            try:
                value = parse_typed(
                    raw,
                    spec.value_type,
                    delimiter=spec.delimiter,
                )

                self.validate_value(
                    spec.name,
                    value,
                )
            except EnvironmentErrorBase as exc:
                errors.append(
                    str(exc)
                )

        return EnvironmentValidationResult(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
            checked=checked,
        )

    # ------------------------------------------------------------------
    # History and listeners
    # ------------------------------------------------------------------

    def history(
        self,
        *,
        limit: int | None = None,
    ) -> list[EnvironmentChange]:
        with self._lock:
            history = list(
                self._history
            )

        if limit is not None:
            return history[
                -max(0, int(limit)):
            ]

        return history

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()

    def add_listener(
        self,
        listener: Callable[
            [EnvironmentChange],
            None,
        ],
    ) -> None:
        if not callable(
            listener
        ):
            raise TypeError(
                "listener must be callable."
            )

        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(
                    listener
                )

    def remove_listener(
        self,
        listener: Callable[
            [EnvironmentChange],
            None,
        ],
    ) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(
                    listener
                )

    def _record_change(
        self,
        change: EnvironmentChange,
    ) -> None:
        with self._lock:
            if self._max_history > 0:
                self._history.append(
                    change
                )

                if (
                    len(self._history)
                    > self._max_history
                ):
                    overflow = (
                        len(self._history)
                        - self._max_history
                    )
                    del self._history[
                        :overflow
                    ]

            listeners = list(
                self._listeners
            )

        for listener in listeners:
            try:
                listener(
                    change
                )
            except Exception:
                # Observers must never break configuration mutation.
                continue

    # ------------------------------------------------------------------
    # Freeze
    # ------------------------------------------------------------------

    def freeze(self) -> None:
        with self._lock:
            self._frozen = True

    def unfreeze(self) -> None:
        with self._lock:
            self._frozen = False

    def _ensure_mutable(self) -> None:
        if self.frozen:
            raise EnvironmentFrozenError(
                "Environment store is frozen."
            )

    # ------------------------------------------------------------------
    # Scoped overrides
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def override(
        self,
        values: Mapping[str, Any],
        *,
        source: str = "temporary",
    ) -> Iterator["EnvironmentStore"]:
        snapshot = self.snapshot()

        self.set_many(
            values,
            source=source,
        )

        try:
            yield self
        finally:
            self.restore(
                snapshot,
                source="temporary_restore",
            )

    # ------------------------------------------------------------------
    # Dotenv integration
    # ------------------------------------------------------------------

    def load_dotenv(
        self,
        path: str | Path,
        *,
        override: bool = False,
        encoding: str = DEFAULT_DOTENV_ENCODING,
    ) -> list[str]:
        values = load_dotenv_file(
            path,
            encoding=encoding,
        )

        loaded: list[str] = []

        for name, value in values.items():
            if (
                not override
                and self.raw_contains(name)
            ):
                continue

            self.raw_set(
                name,
                value,
                source=f"dotenv:{path}",
            )
            loaded.append(
                name
            )

        return loaded

    def dump_dotenv(
        self,
        path: str | Path,
        *,
        prefix: str | None = None,
        include_header: bool = True,
        reveal_secrets: bool = False,
        encoding: str = DEFAULT_DOTENV_ENCODING,
    ) -> Path:
        values = self.to_dict(
            prefix=prefix,
            reveal_secrets=reveal_secrets,
        )

        if not reveal_secrets:
            for name in list(values):
                if is_sensitive_name(name):
                    values[name] = "***"

        target = Path(path)
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            dump_dotenv(
                values,
                include_header=include_header,
            ),
            encoding=encoding,
        )

        return target

    # ------------------------------------------------------------------
    # Export and import
    # ------------------------------------------------------------------

    def export_json(
        self,
        path: str | Path,
        *,
        prefix: str | None = None,
        reveal_secrets: bool = False,
        indent: int = 2,
        encoding: str = "utf-8",
    ) -> Path:
        target = Path(path)
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            json.dumps(
                self.to_dict(
                    prefix=prefix,
                    reveal_secrets=reveal_secrets,
                ),
                indent=indent,
                ensure_ascii=False,
            ),
            encoding=encoding,
        )

        return target

    def import_json(
        self,
        path: str | Path,
        *,
        override: bool = True,
        encoding: str = "utf-8",
    ) -> list[str]:
        source = Path(path)

        try:
            data = json.loads(
                source.read_text(
                    encoding=encoding
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise EnvironmentParseError(
                f"Unable to import environment JSON "
                f"from '{source}'."
            ) from exc

        if not isinstance(
            data,
            Mapping,
        ):
            raise EnvironmentParseError(
                "Environment JSON root must be an object."
            )

        imported: list[str] = []

        for name, value in data.items():
            normalized = normalize_env_name(
                name
            )

            if (
                not override
                and self.raw_contains(
                    normalized
                )
            ):
                continue

            self.set(
                normalized,
                value,
                source=f"json:{source}",
            )
            imported.append(
                normalized
            )

        return imported

    # ------------------------------------------------------------------
    # Search and filtering
    # ------------------------------------------------------------------

    def find(
        self,
        query: str,
        *,
        prefix: str | None = None,
        case_sensitive: bool = False,
    ) -> dict[str, str]:
        needle = str(query)

        if not case_sensitive:
            needle = needle.upper()

        result = {}

        for name, value in self.items(
            prefix=prefix,
            reveal_secrets=True,
        ):
            candidate = (
                name
                if case_sensitive
                else name.upper()
            )

            if needle in candidate:
                result[name] = value

        return result

    def matching(
        self,
        pattern: str,
        *,
        prefix: str | None = None,
        flags: int = 0,
        reveal_secrets: bool = True,
    ) -> dict[str, str]:
        regex = re.compile(
            pattern,
            flags,
        )

        result = {}

        for name, value in self.items(
            prefix=prefix,
            reveal_secrets=reveal_secrets,
        ):
            if regex.search(name):
                result[name] = value

        return result

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def metadata(
        self,
        name: str,
    ) -> dict[str, Any]:
        normalized = self.resolve_alias(
            name
        )

        spec = self.get_spec(
            normalized
        )

        raw = self.raw_get(
            normalized
        )

        return {
            "name": normalized,
            "exists": raw is not None,
            "secret": (
                spec.secret
                if spec is not None
                else is_sensitive_name(normalized)
            ),
            "required": (
                spec.required
                if spec is not None
                else False
            ),
            "type": (
                spec.value_type.value
                if spec is not None
                else EnvironmentValueType.STRING.value
            ),
            "description": (
                spec.description
                if spec is not None
                else ""
            ),
            "default": (
                copy.deepcopy(spec.default)
                if spec is not None
                else None
            ),
        }

    def diagnostics(
        self,
        *,
        prefix: str | None = None,
        reveal_secrets: bool = False,
    ) -> dict[str, Any]:
        values = self.to_dict(
            prefix=prefix,
            reveal_secrets=reveal_secrets,
        )

        if not reveal_secrets:
            for name in list(values):
                if is_sensitive_name(name):
                    values[name] = "***"

        validation = self.validate(
            strict_required=False
        )

        return {
            "prefix": (
                normalize_prefix(prefix)
                if prefix is not None
                else self._prefix
            ),
            "count": len(values),
            "digest": environment_digest(
                {
                    key: str(value)
                    for key, value in values.items()
                }
            ),
            "frozen": self.frozen,
            "mutate_process": self.mutate_process,
            "values": values,
            "validation": {
                "valid": validation.valid,
                "errors": list(validation.errors),
                "warnings": list(validation.warnings),
                "checked": validation.checked,
            },
        }

    # ------------------------------------------------------------------
    # Copy and mapping protocol
    # ------------------------------------------------------------------

    def copy(
        self,
        *,
        isolated: bool = True,
    ) -> "EnvironmentStore":
        if isolated:
            mapping = dict(
                self._environ
            )
        else:
            mapping = self._environ

        clone = EnvironmentStore(
            mapping,
            prefix=self._prefix,
            separator=self._separator,
            max_history=self._max_history,
            mutate_process=(
                False
                if isolated
                else self._mutate_process
            ),
        )

        clone.register_specs(
            self.specs()
        )

        return clone

    def __getitem__(
        self,
        name: str,
    ) -> str:
        value = self.raw_get(
            name
        )

        if value is None:
            raise EnvironmentKeyError(
                f"Environment variable "
                f"'{name}' is missing."
            )

        return value

    def __setitem__(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.raw_set(
            name,
            value,
        )

    def __delitem__(
        self,
        name: str,
    ) -> None:
        if not self.raw_delete(name):
            raise KeyError(
                name
            )

    def __contains__(
        self,
        name: object,
    ) -> bool:
        try:
            return self.raw_contains(
                str(name)
            )
        except Exception:
            return False

    def __iter__(self) -> Iterator[str]:
        return iter(
            self.names()
        )

    def __len__(self) -> int:
        return len(
            self.names()
        )

    def __repr__(self) -> str:
        return (
            "EnvironmentStore("
            f"prefix={self._prefix!r}, "
            f"count={len(self)}, "
            f"frozen={self.frozen})"
        )


# ---------------------------------------------------------------------------
# Namespace view
# ---------------------------------------------------------------------------

class EnvironmentNamespace:
    """Convenient scoped view over a prefixed environment namespace."""

    def __init__(
        self,
        store: EnvironmentStore,
        prefix: str,
    ) -> None:
        self._store = store
        self._prefix = normalize_prefix(
            prefix
        )

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def store(self) -> EnvironmentStore:
        return self._store

    def name(
        self,
        key: str,
    ) -> str:
        return (
            self._prefix
            + normalize_env_name(key)
        )

    def get(
        self,
        key: str,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        return self._store.get(
            self.name(key),
            default,
            **kwargs,
        )

    def require(
        self,
        key: str,
        **kwargs: Any,
    ) -> Any:
        return self._store.require(
            self.name(key),
            **kwargs,
        )

    def set(
        self,
        key: str,
        value: Any,
        **kwargs: Any,
    ) -> None:
        self._store.set(
            self.name(key),
            value,
            **kwargs,
        )

    def delete(
        self,
        key: str,
        **kwargs: Any,
    ) -> bool:
        return self._store.delete(
            self.name(key),
            **kwargs,
        )

    def contains(
        self,
        key: str,
    ) -> bool:
        return self._store.raw_contains(
            self.name(key)
        )

    def names(self) -> list[str]:
        names = self._store.names(
            prefix=self._prefix
        )

        return [
            name[
                len(self._prefix):
            ]
            for name in names
        ]

    def to_dict(
        self,
        *,
        reveal_secrets: bool = False,
    ) -> dict[str, str]:
        values = self._store.to_dict(
            prefix=self._prefix,
            reveal_secrets=reveal_secrets,
        )

        return {
            name[
                len(self._prefix):
            ]: value
            for name, value in values.items()
        }

    def namespace(
        self,
        child: str,
    ) -> "EnvironmentNamespace":
        return EnvironmentNamespace(
            self._store,
            self._prefix
            + normalize_prefix(child),
        )

    def __getitem__(
        self,
        key: str,
    ) -> Any:
        return self.require(key)

    def __setitem__(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.set(
            key,
            value,
        )

    def __contains__(
        self,
        key: object,
    ) -> bool:
        return self.contains(
            str(key)
        )


# ---------------------------------------------------------------------------
# Global environment store and helpers
# ---------------------------------------------------------------------------

environment = EnvironmentStore()


def get_env(
    name: str,
    default: Any = None,
    **kwargs: Any,
) -> Any:
    """Read an environment value."""
    return environment.get(
        name,
        default,
        **kwargs,
    )


def require_env(
    name: str,
    **kwargs: Any,
) -> Any:
    """Read a required environment value."""
    return environment.require(
        name,
        **kwargs,
    )


def set_env(
    name: str,
    value: Any,
    **kwargs: Any,
) -> None:
    """Set an environment value."""
    environment.set(
        name,
        value,
        **kwargs,
    )


def delete_env(
    name: str,
    **kwargs: Any,
) -> bool:
    """Delete an environment value."""
    return environment.delete(
        name,
        **kwargs,
    )


def env_namespace(
    prefix: str,
) -> EnvironmentNamespace:
    """Create a scoped environment namespace."""
    return EnvironmentNamespace(
        environment,
        prefix,
    )


def load_environment_file(
    path: str | Path,
    *,
    override: bool = False,
    encoding: str = DEFAULT_DOTENV_ENCODING,
) -> list[str]:
    """Load a dotenv file into the global environment store."""
    return environment.load_dotenv(
        path,
        override=override,
        encoding=encoding,
    )


def environment_snapshot(
    *,
    prefix: str | None = None,
) -> EnvironmentSnapshot:
    """Create a snapshot of the global environment."""
    return environment.snapshot(
        prefix=prefix
    )


def environment_validation() -> EnvironmentValidationResult:
    """Validate registered global environment specifications."""
    return environment.validate()


def freeze_environment() -> None:
    """Freeze the global environment abstraction."""
    environment.freeze()


def unfreeze_environment() -> None:
    """Unfreeze the global environment abstraction."""
    environment.unfreeze()


# ---------------------------------------------------------------------------
# Standard AURA specifications
# ---------------------------------------------------------------------------

DEFAULT_ENVIRONMENT_SPECS = (
    EnvironmentSpec(
        name="AURA_ENV",
        value_type=EnvironmentValueType.STRING,
        default="development",
        description="AURA runtime environment.",
        choices=(
            "development",
            "testing",
            "staging",
            "production",
        ),
    ),
    EnvironmentSpec(
        name="AURA_DEBUG",
        value_type=EnvironmentValueType.BOOLEAN,
        default=False,
        description="Enable AURA debug behavior.",
    ),
    EnvironmentSpec(
        name="AURA_LOG_LEVEL",
        value_type=EnvironmentValueType.STRING,
        default="INFO",
        description="Default AURA log level.",
        choices=(
            "TRACE",
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ),
    ),
    EnvironmentSpec(
        name="AURA_SERIALIZATION_FORMAT",
        value_type=EnvironmentValueType.STRING,
        default="json",
        description="Default serialization format.",
    ),
    EnvironmentSpec(
        name="AURA_SERIALIZATION_ENCODING",
        value_type=EnvironmentValueType.STRING,
        default="utf-8",
        description="Default text encoding.",
    ),
    EnvironmentSpec(
        name="AURA_SERIALIZATION_STRICT",
        value_type=EnvironmentValueType.BOOLEAN,
        default=False,
        description="Enable strict serialization behavior.",
    ),
    EnvironmentSpec(
        name="AURA_CACHE_ENABLED",
        value_type=EnvironmentValueType.BOOLEAN,
        default=True,
        description="Enable AURA caching.",
    ),
    EnvironmentSpec(
        name="AURA_CACHE_SIZE",
        value_type=EnvironmentValueType.INTEGER,
        default=256,
        minimum=0,
        description="Default cache capacity.",
    ),
    EnvironmentSpec(
        name="AURA_WORKERS",
        value_type=EnvironmentValueType.INTEGER,
        default=1,
        minimum=1,
        description="Default worker count.",
    ),
    EnvironmentSpec(
        name="AURA_HOST",
        value_type=EnvironmentValueType.STRING,
        default="127.0.0.1",
        description="Default service bind host.",
    ),
    EnvironmentSpec(
        name="AURA_PORT",
        value_type=EnvironmentValueType.INTEGER,
        default=8000,
        minimum=1,
        maximum=65535,
        description="Default service bind port.",
    ),
    EnvironmentSpec(
        name="AURA_DATABASE_URL",
        value_type=EnvironmentValueType.STRING,
        default=None,
        description="Database connection URL.",
        secret=True,
        nullable=True,
    ),
    EnvironmentSpec(
        name="AURA_API_KEY",
        value_type=EnvironmentValueType.STRING,
        default=None,
        description="External API credential.",
        secret=True,
        nullable=True,
    ),
)


def register_default_specs(
    store: EnvironmentStore | None = None,
    *,
    replace: bool = False,
) -> list[EnvironmentSpec]:
    """Register the standard AURA environment specifications."""
    target = (
        store
        if store is not None
        else environment
    )

    return target.register_specs(
        DEFAULT_ENVIRONMENT_SPECS,
        replace=replace,
    )


# Register defaults at import time. This only registers metadata and
# does not overwrite values already present in os.environ.
register_default_specs(
    environment
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "DEFAULT_PREFIX",
    "DEFAULT_SEPARATOR",
    "DEFAULT_DOTENV_ENCODING",
    "DEFAULT_MAX_HISTORY",
    "TRUE_VALUES",
    "FALSE_VALUES",
    "NULL_VALUES",
    "SENSITIVE_NAME_PARTS",
    "EnvironmentErrorBase",
    "EnvironmentKeyError",
    "EnvironmentParseError",
    "EnvironmentValidationError",
    "EnvironmentMutationError",
    "DotenvParseError",
    "EnvironmentFrozenError",
    "EnvironmentValueType",
    "EnvironmentChangeType",
    "EnvironmentSpec",
    "EnvironmentValue",
    "EnvironmentChange",
    "EnvironmentSnapshot",
    "EnvironmentDiff",
    "EnvironmentValidationResult",
    "normalize_env_name",
    "normalize_prefix",
    "environment_name",
    "is_sensitive_name",
    "mask_secret",
    "environment_digest",
    "parse_bool",
    "parse_int",
    "parse_float",
    "parse_json",
    "parse_path",
    "parse_list",
    "parse_set",
    "parse_typed",
    "serialize_typed",
    "strip_inline_comment",
    "unquote_value",
    "parse_dotenv_line",
    "parse_dotenv",
    "load_dotenv_file",
    "quote_dotenv_value",
    "dump_dotenv",
    "EnvironmentStore",
    "EnvironmentNamespace",
    "environment",
    "get_env",
    "require_env",
    "set_env",
    "delete_env",
    "env_namespace",
    "load_environment_file",
    "environment_snapshot",
    "environment_validation",
    "freeze_environment",
    "unfreeze_environment",
    "DEFAULT_ENVIRONMENT_SPECS",
    "register_default_specs",
]


# ---------------------------------------------------------------------------
# Additional production convenience accessors
# ---------------------------------------------------------------------------

def _get_nonempty_string(
    self: EnvironmentStore,
    name: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str | None:
    value = self.get_string(
        name,
        default,
        required=required,
    )

    if value is None:
        return None

    value = value.strip()

    if not value and required:
        raise EnvironmentValidationError(
            f"Environment variable '{name}' cannot be empty."
        )

    return value


def _get_url(
    self: EnvironmentStore,
    name: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str | None:
    value = _get_nonempty_string(
        self,
        name,
        default,
        required=required,
    )

    if value is None:
        return None

    if "://" not in value:
        raise EnvironmentValidationError(
            f"Environment variable '{name}' must contain a URL scheme."
        )

    return value


def _get_port(
    self: EnvironmentStore,
    name: str,
    default: int | None = None,
    *,
    required: bool = False,
) -> int | None:
    value = self.get_int(
        name,
        default,
        required=required,
    )

    if value is None:
        return None

    if not 1 <= value <= 65535:
        raise EnvironmentValidationError(
            f"Environment variable '{name}' must be "
            "between 1 and 65535."
        )

    return value


def _get_percentage(
    self: EnvironmentStore,
    name: str,
    default: float | None = None,
    *,
    required: bool = False,
) -> float | None:
    value = self.get_float(
        name,
        default,
        required=required,
    )

    if value is None:
        return None

    if not 0.0 <= value <= 100.0:
        raise EnvironmentValidationError(
            f"Environment variable '{name}' must be "
            "between 0 and 100."
        )

    return value


def _get_choice(
    self: EnvironmentStore,
    name: str,
    choices: Sequence[str],
    default: str | None = None,
    *,
    required: bool = False,
) -> str | None:
    value = self.get_string(
        name,
        default,
        required=required,
    )

    if value is None:
        return None

    if value not in choices:
        raise EnvironmentValidationError(
            f"Environment variable '{name}' must be one of "
            f"{tuple(choices)!r}."
        )

    return value


def _get_csv(
    self: EnvironmentStore,
    name: str,
    default: Sequence[str] | None = None,
    *,
    required: bool = False,
    delimiter: str = ",",
) -> list[str] | None:
    return self.get_list(
        name,
        default,
        delimiter=delimiter,
        required=required,
    )


def _get_duration_seconds(
    self: EnvironmentStore,
    name: str,
    default: float | None = None,
    *,
    required: bool = False,
) -> float | None:
    raw = self.get_string(
        name,
        None,
        required=required,
    )

    if raw is None:
        return default

    text = raw.strip().lower()

    units = (
        ("ms", 0.001),
        ("s", 1.0),
        ("m", 60.0),
        ("h", 3600.0),
        ("d", 86400.0),
    )

    for suffix, multiplier in units:
        if text.endswith(suffix):
            number = text[:-len(suffix)].strip()
            try:
                return float(number) * multiplier
            except ValueError as exc:
                raise EnvironmentParseError(
                    f"Invalid duration '{raw}'."
                ) from exc

    try:
        return float(text)
    except ValueError as exc:
        raise EnvironmentParseError(
            f"Invalid duration '{raw}'."
        ) from exc


def _get_bytes(
    self: EnvironmentStore,
    name: str,
    default: int | None = None,
    *,
    required: bool = False,
) -> int | None:
    raw = self.get_string(
        name,
        None,
        required=required,
    )

    if raw is None:
        return default

    text = raw.strip().upper()

    units = (
        ("KIB", 1024),
        ("MIB", 1024 ** 2),
        ("GIB", 1024 ** 3),
        ("KB", 1000),
        ("MB", 1000 ** 2),
        ("GB", 1000 ** 3),
        ("B", 1),
    )

    for suffix, multiplier in units:
        if text.endswith(suffix):
            number = text[:-len(suffix)].strip()
            try:
                return int(float(number) * multiplier)
            except ValueError as exc:
                raise EnvironmentParseError(
                    f"Invalid byte size '{raw}'."
                ) from exc

    try:
        return int(text)
    except ValueError as exc:
        raise EnvironmentParseError(
            f"Invalid byte size '{raw}'."
        ) from exc


def _get_log_level(
    self: EnvironmentStore,
    name: str = "AURA_LOG_LEVEL",
    default: str = "INFO",
) -> str:
    levels = (
        "TRACE",
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    )

    value = self.get_string(
        name,
        default,
    )

    if value is None:
        return default

    normalized = value.strip().upper()

    if normalized not in levels:
        raise EnvironmentValidationError(
            f"Unsupported log level '{value}'."
        )

    return normalized


def _get_environment_name(
    self: EnvironmentStore,
    name: str = "AURA_ENV",
    default: str = "development",
) -> str:
    environments = (
        "development",
        "testing",
        "staging",
        "production",
    )

    value = self.get_string(
        name,
        default,
    )

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized not in environments:
        raise EnvironmentValidationError(
            f"Unsupported environment '{value}'."
        )

    return normalized


def _is_production(
    self: EnvironmentStore,
) -> bool:
    return (
        self.get_environment_name()
        == "production"
    )


def _is_debug(
    self: EnvironmentStore,
) -> bool:
    return self.get_bool(
        "AURA_DEBUG",
        False,
    ) is True


def _secret_names(
    self: EnvironmentStore,
    *,
    prefix: str | None = None,
) -> list[str]:
    return [
        name
        for name in self.names(
            prefix=prefix
        )
        if is_sensitive_name(name)
    ]


def _safe_dict(
    self: EnvironmentStore,
    *,
    prefix: str | None = None,
) -> dict[str, str]:
    return self.to_dict(
        prefix=prefix,
        reveal_secrets=False,
    )


def _set_default(
    self: EnvironmentStore,
    name: str,
    value: Any,
    *,
    value_type: EnvironmentValueType | None = None,
) -> bool:
    if self.raw_contains(name):
        return False

    self.set(
        name,
        value,
        value_type=value_type,
        source="default",
    )
    return True


def _set_if_missing(
    self: EnvironmentStore,
    name: str,
    value: Any,
    *,
    value_type: EnvironmentValueType | None = None,
) -> bool:
    return _set_default(
        self,
        name,
        value,
        value_type=value_type,
    )


def _update_from_mapping(
    self: EnvironmentStore,
    values: Mapping[str, Any],
    *,
    source: str = "mapping",
    override: bool = True,
) -> list[str]:
    updated = []

    for name, value in values.items():
        normalized = normalize_env_name(name)

        if (
            not override
            and self.raw_contains(normalized)
        ):
            continue

        self.set(
            normalized,
            value,
            source=source,
        )
        updated.append(normalized)

    return updated


def _copy_from(
    self: EnvironmentStore,
    other: EnvironmentStore,
    *,
    prefix: str | None = None,
    override: bool = True,
) -> list[str]:
    return _update_from_mapping(
        self,
        other.to_dict(
            prefix=prefix,
            reveal_secrets=True,
        ),
        source=f"store:{id(other)}",
        override=override,
    )


def _has_any(
    self: EnvironmentStore,
    names: Iterable[str],
) -> bool:
    return any(
        self.raw_contains(name)
        for name in names
    )


def _has_all(
    self: EnvironmentStore,
    names: Iterable[str],
) -> bool:
    return all(
        self.raw_contains(name)
        for name in names
    )


def _require_all(
    self: EnvironmentStore,
    names: Iterable[str],
) -> dict[str, Any]:
    result = {}

    for name in names:
        result[name] = self.require(name)

    return result


def _require_any(
    self: EnvironmentStore,
    names: Iterable[str],
) -> tuple[str, Any]:
    for name in names:
        if self.raw_contains(name):
            return (
                name,
                self.require(name),
            )

    raise EnvironmentKeyError(
        "None of the required environment variables "
        f"were found: {tuple(names)!r}"
    )


def _changed_since(
    self: EnvironmentStore,
    snapshot: EnvironmentSnapshot,
) -> EnvironmentDiff:
    return self.diff(
        snapshot,
        self.snapshot(
            prefix=snapshot.prefix
        ),
    )


def _has_changed(
    self: EnvironmentStore,
    snapshot: EnvironmentSnapshot,
) -> bool:
    return not self.changed_since(
        snapshot
    ).is_empty


def _environment_summary(
    self: EnvironmentStore,
) -> dict[str, Any]:
    validation = self.validate(
        strict_required=False
    )

    return {
        "prefix": self.prefix,
        "count": len(self),
        "spec_count": len(self.specs()),
        "frozen": self.frozen,
        "valid": validation.valid,
        "error_count": len(validation.errors),
        "warning_count": len(validation.warnings),
        "secret_count": len(
            self.secret_names()
        ),
        "digest": environment_digest(
            {
                key: value
                for key, value
                in self.items(
                    reveal_secrets=True
                )
            }
        ),
    }


# Bind the additional methods explicitly. Keeping these bindings near the
# implementation makes the public EnvironmentStore API easy to audit.
EnvironmentStore.get_nonempty_string = _get_nonempty_string
EnvironmentStore.get_url = _get_url
EnvironmentStore.get_port = _get_port
EnvironmentStore.get_percentage = _get_percentage
EnvironmentStore.get_choice = _get_choice
EnvironmentStore.get_csv = _get_csv
EnvironmentStore.get_duration_seconds = _get_duration_seconds
EnvironmentStore.get_bytes = _get_bytes
EnvironmentStore.get_log_level = _get_log_level
EnvironmentStore.get_environment_name = _get_environment_name
EnvironmentStore.is_production = _is_production
EnvironmentStore.is_debug = _is_debug
EnvironmentStore.secret_names = _secret_names
EnvironmentStore.safe_dict = _safe_dict
EnvironmentStore.set_default = _set_default
EnvironmentStore.set_if_missing = _set_if_missing
EnvironmentStore.update_from_mapping = _update_from_mapping
EnvironmentStore.copy_from = _copy_from
EnvironmentStore.has_any = _has_any
EnvironmentStore.has_all = _has_all
EnvironmentStore.require_all = _require_all
EnvironmentStore.require_any = _require_any
EnvironmentStore.changed_since = _changed_since
EnvironmentStore.has_changed = _has_changed
EnvironmentStore.summary = _environment_summary


# ---------------------------------------------------------------------------
# Additional namespace utilities
# ---------------------------------------------------------------------------

def namespace_value(
    store: EnvironmentStore,
    prefix: str,
    key: str,
    default: Any = None,
) -> Any:
    """Read one value from a named environment namespace."""
    return EnvironmentNamespace(
        store,
        prefix,
    ).get(
        key,
        default,
    )


def namespace_values(
    store: EnvironmentStore,
    prefix: str,
    *,
    reveal_secrets: bool = False,
) -> dict[str, str]:
    """Read all values from a namespace."""
    return EnvironmentNamespace(
        store,
        prefix,
    ).to_dict(
        reveal_secrets=reveal_secrets
    )


def environment_contains_prefix(
    prefix: str,
    *,
    store: EnvironmentStore | None = None,
) -> bool:
    """Return whether the environment contains a given prefix."""
    target = store or environment
    return bool(
        target.names(
            prefix=prefix
        )
    )


def compare_environments(
    first: EnvironmentStore,
    second: EnvironmentStore,
    *,
    prefix: str | None = None,
) -> EnvironmentDiff:
    """Compare two environment stores."""
    return EnvironmentStore.diff(
        first.snapshot(
            prefix=prefix
        ),
        second.snapshot(
            prefix=prefix
        ),
    )


def clone_environment(
    store: EnvironmentStore | None = None,
) -> EnvironmentStore:
    """Create an isolated copy of an environment store."""
    return (
        store or environment
    ).copy(
        isolated=True
    )


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def temporary_environment(
    values: Mapping[str, Any],
    *,
    store: EnvironmentStore | None = None,
) -> Iterator[EnvironmentStore]:
    """Temporarily apply environment values."""
    target = store or environment

    with target.override(
        values
    ) as active:
        yield active


@contextlib.contextmanager
def isolated_environment(
    values: Mapping[str, Any] | None = None,
    *,
    prefix: str = DEFAULT_PREFIX,
) -> Iterator[EnvironmentStore]:
    """Create an isolated environment store for tests or staging."""
    mapping = dict(
        values or {}
    )

    store = EnvironmentStore(
        mapping,
        prefix=prefix,
        mutate_process=False,
    )

    yield store


# ---------------------------------------------------------------------------
# Extended public API additions
# ---------------------------------------------------------------------------

__all__.extend([
    "namespace_value",
    "namespace_values",
    "environment_contains_prefix",
    "compare_environments",
    "clone_environment",
    "temporary_environment",
    "isolated_environment",
])


# ---------------------------------------------------------------------------
# Global AURA environment convenience API
# ---------------------------------------------------------------------------

def aura_environment() -> str:
    """Return the normalized AURA runtime environment."""
    return environment.get_environment_name()


def aura_debug() -> bool:
    """Return whether AURA debug mode is enabled."""
    return environment.is_debug()


def aura_log_level() -> str:
    """Return the normalized AURA log level."""
    return environment.get_log_level()


def aura_serialization_format() -> str:
    """Return the configured serialization format."""
    return environment.get_string(
        "AURA_SERIALIZATION_FORMAT",
        "json",
    ) or "json"


def aura_serialization_encoding() -> str:
    """Return the configured serialization encoding."""
    return environment.get_string(
        "AURA_SERIALIZATION_ENCODING",
        "utf-8",
    ) or "utf-8"


def aura_serialization_strict() -> bool:
    """Return whether strict serialization is enabled."""
    return environment.get_bool(
        "AURA_SERIALIZATION_STRICT",
        False,
    ) is True


def aura_cache_enabled() -> bool:
    """Return whether caching is enabled."""
    return environment.get_bool(
        "AURA_CACHE_ENABLED",
        True,
    ) is True


def aura_cache_size() -> int:
    """Return the configured cache size."""
    return environment.get_int(
        "AURA_CACHE_SIZE",
        256,
    ) or 256


def aura_workers() -> int:
    """Return the configured worker count."""
    return environment.get_int(
        "AURA_WORKERS",
        1,
    ) or 1


def aura_host() -> str:
    """Return the configured service host."""
    return (
        environment.get_string(
            "AURA_HOST",
            "127.0.0.1",
        )
        or "127.0.0.1"
    )


def aura_port() -> int:
    """Return the configured service port."""
    return (
        environment.get_port(
            "AURA_PORT",
            8000,
        )
        or 8000
    )


def aura_database_url() -> str | None:
    """Return the database URL."""
    return environment.get_string(
        "AURA_DATABASE_URL"
    )


def aura_api_key() -> str | None:
    """Return the configured API key."""
    return environment.get_string(
        "AURA_API_KEY"
    )


__all__.extend([
    "aura_environment",
    "aura_debug",
    "aura_log_level",
    "aura_serialization_format",
    "aura_serialization_encoding",
    "aura_serialization_strict",
    "aura_cache_enabled",
    "aura_cache_size",
    "aura_workers",
    "aura_host",
    "aura_port",
    "aura_database_url",
    "aura_api_key",
])