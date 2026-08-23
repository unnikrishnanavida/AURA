"""
AURA Foundation - Dotenv Serializer.

Serializer for .env-style configuration files.

The codec supports:
- KEY=VALUE records
- comments
- quoted values
- multiline values
- environment expansion
- typed conversion
- export/import helpers
- file and stream operations
- batch operations
- async operations
- gzip compression
- bounded caching
- metrics
- diagnostics
- lifecycle and registry integration
"""

from __future__ import annotations

import asyncio
import gzip
import io
import json
import os
import re
import threading
import time

from collections import OrderedDict
from pathlib import Path
from typing import Any, IO, Iterable, Mapping, Sequence

try:
    from .interfaces import BaseCodec
except ImportError:
    class BaseCodec:
        pass

try:
    from .models import (
        SerializationRequest,
        SerializationResponse,
        DeserializationRequest,
        DeserializationResponse,
    )
except ImportError:
    SerializationRequest = Any
    SerializationResponse = Any
    DeserializationRequest = Any
    DeserializationResponse = Any

try:
    from .constants import SerializationFormat
except ImportError:
    class SerializationFormat:
        DOTENV = "dotenv"

try:
    from .exceptions import SerializationError, DeserializationError
except ImportError:
    class SerializationError(Exception):
        pass

    class DeserializationError(Exception):
        pass

try:
    from .utilities import current_iso_timestamp
except ImportError:
    def current_iso_timestamp() -> str:
        return time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(),
        )

try:
    from .version import VERSION
except ImportError:
    VERSION = "1.0.0"


class DotenvCodec(BaseCodec):
    """Codec for conventional .env configuration files."""

    _KEY_RE = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    _ENV_RE = re.compile(
        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"
    )

    _BARE_ENV_RE = re.compile(
        r"\$([A-Za-z_][A-Za-z0-9_]*)"
    )

    DEFAULT_ENCODING = "utf-8"
    DEFAULT_CACHE_SIZE = 256
    DEFAULT_EXPORT_PREFIX = ""
    DEFAULT_SORT_KEYS = False
    DEFAULT_SPACE_AROUND_EQUALS = False
    DEFAULT_QUOTE_VALUES = False

    def __init__(
        self,
        *,
        encoding: str = DEFAULT_ENCODING,
        cache_size: int = DEFAULT_CACHE_SIZE,
        export_prefix: str = DEFAULT_EXPORT_PREFIX,
        sort_keys: bool = DEFAULT_SORT_KEYS,
        space_around_equals: bool = DEFAULT_SPACE_AROUND_EQUALS,
        quote_values: bool = DEFAULT_QUOTE_VALUES,
    ) -> None:
        if cache_size < 0:
            raise ValueError(
                "cache_size cannot be negative"
            )

        self._encoding = encoding
        self._cache_size = int(cache_size)
        self._export_prefix = export_prefix
        self._sort_keys = bool(sort_keys)
        self._space_around_equals = bool(
            space_around_equals
        )
        self._quote_values = bool(quote_values)

        self._serialization_count = 0
        self._deserialization_count = 0
        self._serialization_time = 0.0
        self._deserialization_time = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        self._bytes_serialized = 0
        self._bytes_deserialized = 0

        self._lock = threading.RLock()
        self._cache: OrderedDict[str, str] = OrderedDict()

    # ==========================================================
    # Identity
    # ==========================================================

    @property
    def name(self) -> str:
        return "dotenv"

    @property
    def format(self) -> str:
        value = getattr(
            SerializationFormat,
            "DOTENV",
            "dotenv",
        )
        return getattr(value, "value", value)

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def cache_size(self) -> int:
        return self._cache_size

    # ==========================================================
    # Configuration
    # ==========================================================

    def configuration(self) -> dict[str, Any]:
        return {
            "encoding": self._encoding,
            "cache_size": self._cache_size,
            "export_prefix": self._export_prefix,
            "sort_keys": self._sort_keys,
            "space_around_equals":
                self._space_around_equals,
            "quote_values": self._quote_values,
        }

    def set_encoding(self, encoding: str) -> None:
        "".encode(encoding)
        self._encoding = encoding
        self.clear_cache()

    def set_cache_size(self, size: int) -> None:
        if size < 0:
            raise ValueError(
                "cache_size cannot be negative"
            )

        with self._lock:
            self._cache_size = int(size)

            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    def set_export_prefix(self, prefix: str) -> None:
        self._export_prefix = str(prefix)
        self.clear_cache()

    def set_sort_keys(self, enabled: bool) -> None:
        self._sort_keys = bool(enabled)
        self.clear_cache()

    def set_quote_values(self, enabled: bool) -> None:
        self._quote_values = bool(enabled)
        self.clear_cache()

    # ==========================================================
    # Key Validation
    # ==========================================================

    @classmethod
    def is_valid_key(cls, key: str) -> bool:
        return bool(
            cls._KEY_RE.fullmatch(str(key))
        )

    @classmethod
    def validate_keys(
        cls,
        mapping: Mapping[str, Any],
    ) -> bool:
        if not isinstance(mapping, Mapping):
            return False

        return all(
            cls.is_valid_key(str(key))
            for key in mapping
        )

    @classmethod
    def normalize_key(cls, key: Any) -> str:
        value = str(key).strip()

        if not cls.is_valid_key(value):
            raise SerializationError(
                f"Invalid dotenv key: {value!r}"
            )

        return value

    # ==========================================================
    # Value Formatting
    # ==========================================================

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(
            value,
            (dict, list, tuple),
        ):
            return json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )

        return str(value)

    @staticmethod
    def _needs_quotes(value: str) -> bool:
        if not value:
            return True

        if value != value.strip():
            return True

        return any(
            char in value
            for char in (
                "#",
                "\n",
                "\r",
                "\t",
                '"',
                "'",
            )
        )

    @staticmethod
    def escape_value(value: str) -> str:
        result: list[str] = []

        for char in value:
            if char == "\\":
                result.append("\\\\")
            elif char == '"':
                result.append('\\"')
            elif char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(char)

        return "".join(result)

    @staticmethod
    def unescape_value(value: str) -> str:
        result: list[str] = []
        index = 0

        while index < len(value):
            char = value[index]

            if char != "\\":
                result.append(char)
                index += 1
                continue

            index += 1

            if index >= len(value):
                result.append("\\")
                break

            escaped = value[index]

            mapping = {
                "n": "\n",
                "r": "\r",
                "t": "\t",
                "\\": "\\",
                '"': '"',
                "'": "'",
                "$": "$",
            }

            result.append(
                mapping.get(
                    escaped,
                    escaped,
                )
            )

            index += 1

        return "".join(result)

    def format_value(self, value: Any) -> str:
        text = self._stringify(value)

        if self._quote_values or self._needs_quotes(text):
            return (
                '"'
                + self.escape_value(text)
                + '"'
            )

        return text

    # ==========================================================
    # Typed Conversion
    # ==========================================================

    @staticmethod
    def convert_value(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        text = value.strip()

        if text.lower() in {
            "true",
            "yes",
            "on",
        }:
            return True

        if text.lower() in {
            "false",
            "no",
            "off",
        }:
            return False

        if text.lower() in {
            "null",
            "none",
        }:
            return None

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            pass

        if text.startswith(
            ("{", "[")
        ):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        return value

    # ==========================================================
    # Quote Parsing
    # ==========================================================

    @classmethod
    def _strip_quotes(
        cls,
        value: str,
    ) -> str:
        text = value.strip()

        if len(text) >= 2:
            if (
                text[0] == '"'
                and text[-1] == '"'
            ):
                return cls.unescape_value(
                    text[1:-1]
                )

            if (
                text[0] == "'"
                and text[-1] == "'"
            ):
                return text[1:-1]

        return cls.unescape_value(text)

    # ==========================================================
    # Comment Handling
    # ==========================================================

    @staticmethod
    def _is_comment(line: str) -> bool:
        stripped = line.lstrip()

        return (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith(";")
        )

    @staticmethod
    def _remove_inline_comment(
        value: str,
    ) -> str:
        quoted = False
        quote = ""
        escaped = False

        for index, char in enumerate(value):
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char in ('"', "'"):
                if not quoted:
                    quoted = True
                    quote = char
                elif quote == char:
                    quoted = False

                continue

            if char == "#" and not quoted:
                if index == 0 or value[index - 1].isspace():
                    return value[:index].rstrip()

        return value.rstrip()

    # ==========================================================
    # Assignment Parsing
    # ==========================================================

    @classmethod
    def _split_assignment(
        cls,
        line: str,
    ) -> tuple[str, str]:
        escaped = False
        quoted = False
        quote = ""

        for index, char in enumerate(line):
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char in ('"', "'"):
                if not quoted:
                    quoted = True
                    quote = char
                elif quote == char:
                    quoted = False
                continue

            if char == "=" and not quoted:
                key = line[:index].strip()
                value = line[index + 1:].strip()
                return key, value

        raise DeserializationError(
            f"Invalid dotenv assignment: {line!r}"
        )

    # ==========================================================
    # Continuation Handling
    # ==========================================================

    @staticmethod
    def _has_continuation(line: str) -> bool:
        count = 0

        for char in reversed(line.rstrip("\r\n")):
            if char == "\\":
                count += 1
            else:
                break

        return count % 2 == 1

    @classmethod
    def _join_continuations(
        cls,
        lines: Iterable[str],
    ) -> list[str]:
        result: list[str] = []
        current = ""

        for line in lines:
            if current:
                current += line.lstrip()
            else:
                current = line

            if cls._has_continuation(current):
                current = current.rstrip()
                current = current[:-1]
                continue

            result.append(current)
            current = ""

        if current:
            result.append(current)

        return result

    # ==========================================================
    # Core Serialization
    # ==========================================================

    def serialize(
        self,
        value: Mapping[str, Any],
        *,
        context: Any = None,
    ) -> str:
        start = time.perf_counter()

        try:
            if not isinstance(value, Mapping):
                raise SerializationError(
                    "dotenv serialization requires a mapping."
                )

            if not self.validate_keys(value):
                raise SerializationError(
                    "One or more dotenv keys are invalid."
                )

            items = list(value.items())

            if self._sort_keys:
                items.sort(
                    key=lambda item: str(item[0])
                )

            lines: list[str] = []

            for key, item_value in items:
                normalized_key = self.normalize_key(key)
                formatted = self.format_value(
                    item_value
                )

                separator = "="

                if self._space_around_equals:
                    separator = " = "

                lines.append(
                    normalized_key
                    + separator
                    + formatted
                )

            result = "\n".join(lines)

            if result:
                result += "\n"

            self._bytes_serialized += len(
                result.encode(self._encoding)
            )

            return result

        except SerializationError:
            raise
        except Exception as exc:
            raise SerializationError(str(exc)) from exc
        finally:
            self._serialization_count += 1
            self._serialization_time += (
                time.perf_counter() - start
            )

    # ==========================================================
    # Core Deserialization
    # ==========================================================

    def deserialize(
        self,
        data: str | bytes,
        *,
        context: Any = None,
        typed: bool = False,
        expand_environment: bool = False,
        environment: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        try:
            if isinstance(data, bytes):
                data = data.decode(
                    self._encoding
                )

            if not isinstance(data, str):
                raise DeserializationError(
                    "dotenv data must be str or bytes."
                )

            result: dict[str, Any] = {}

            lines = self._join_continuations(
                data.splitlines()
            )

            for line in lines:
                if self._is_comment(line):
                    continue

                key, raw_value = self._split_assignment(
                    line.strip()
                )

                key = key.strip()

                if key.startswith("export "):
                    key = key[7:].strip()

                key = self.normalize_key(key)

                raw_value = self._remove_inline_comment(
                    raw_value
                )

                value = self._strip_quotes(
                    raw_value
                )

                if expand_environment:
                    value = self.expand_environment(
                        value,
                        environment,
                    )

                if typed:
                    value = self.convert_value(
                        value
                    )

                result[key] = value

            self._bytes_deserialized += len(
                data.encode(self._encoding)
            )

            return result

        except DeserializationError:
            raise
        except Exception as exc:
            raise DeserializationError(str(exc)) from exc
        finally:
            self._deserialization_count += 1
            self._deserialization_time += (
                time.perf_counter() - start
            )

    # ==========================================================
    # Request / Response
    # ==========================================================

    def serialize_request(
        self,
        request: SerializationRequest,
    ) -> SerializationResponse:
        data = self.serialize(
            request.value
        )

        return SerializationResponse(
            data=data,
            format=self.format,
            encoding=getattr(
                request,
                "encoding",
                self._encoding,
            ),
            compressed=getattr(
                request,
                "compress",
                False,
            ),
            encrypted=getattr(
                request,
                "encrypt",
                False,
            ),
            metadata={
                "serializer": self.name,
                "timestamp":
                    current_iso_timestamp(),
            },
        )

    def deserialize_request(
        self,
        request: DeserializationRequest,
    ) -> DeserializationResponse:
        value = self.deserialize(
            request.data
        )

        return DeserializationResponse(
            value=value,
            metadata=getattr(
                request,
                "metadata",
                {},
            ),
            valid=True,
        )

    # ==========================================================
    # Environment Expansion
    # ==========================================================

    @classmethod
    def expand_environment(
        cls,
        value: str,
        environment: Mapping[str, str] | None = None,
        *,
        missing: str = "preserve",
    ) -> str:
        source = (
            environment
            if environment is not None
            else os.environ
        )

        def replace_braced(
            match: re.Match[str],
        ) -> str:
            name = match.group(1)

            if name in source:
                return str(source[name])

            if missing == "empty":
                return ""

            if missing == "error":
                raise KeyError(name)

            return match.group(0)

        value = cls._ENV_RE.sub(
            replace_braced,
            value,
        )

        def replace_bare(
            match: re.Match[str],
        ) -> str:
            name = match.group(1)

            if name in source:
                return str(source[name])

            if missing == "empty":
                return ""

            if missing == "error":
                raise KeyError(name)

            return match.group(0)

        return cls._BARE_ENV_RE.sub(
            replace_bare,
            value,
        )

    def expand_mapping(
        self,
        mapping: Mapping[str, Any],
        environment: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            str(key): (
                self.expand_environment(
                    value,
                    environment,
                )
                if isinstance(value, str)
                else value
            )
            for key, value in mapping.items()
        }

    # ==========================================================
    # Environment Export
    # ==========================================================

    def export_environment(
        self,
        mapping: Mapping[str, Any],
        *,
        prefix: str | None = None,
    ) -> dict[str, str]:
        active_prefix = (
            self._export_prefix
            if prefix is None
            else str(prefix)
        )

        result: dict[str, str] = {}

        for key, value in mapping.items():
            name = self.normalize_key(key)

            if active_prefix:
                name = (
                    active_prefix
                    + name
                )

            result[name] = self._stringify(
                value
            )

        return result

    def load_environment(
        self,
        mapping: Mapping[str, Any],
        *,
        prefix: str | None = None,
        overwrite: bool = False,
        target: dict[str, str] | None = None,
    ) -> dict[str, str]:
        destination = (
            target
            if target is not None
            else dict(os.environ)
        )

        exported = self.export_environment(
            mapping,
            prefix=prefix,
        )

        for key, value in exported.items():
            if overwrite or key not in destination:
                destination[key] = value

        return destination

    # ==========================================================
    # File API
    # ==========================================================

    def serialize_to_file(
        self,
        value: Mapping[str, Any],
        path: str | Path,
    ) -> Path:
        target = Path(path)

        target.write_text(
            self.serialize(value),
            encoding=self._encoding,
            newline="",
        )

        return target

    def deserialize_from_file(
        self,
        path: str | Path,
        *,
        typed: bool = False,
        expand_environment: bool = False,
    ) -> dict[str, Any]:
        data = Path(path).read_text(
            encoding=self._encoding
        )

        return self.deserialize(
            data,
            typed=typed,
            expand_environment=expand_environment,
        )

    # ==========================================================
    # Stream API
    # ==========================================================

    def serialize_to_stream(
        self,
        value: Mapping[str, Any],
        stream: IO[str],
    ) -> None:
        stream.write(
            self.serialize(value)
        )

    def deserialize_from_stream(
        self,
        stream: IO[str],
        *,
        typed: bool = False,
        expand_environment: bool = False,
    ) -> dict[str, Any]:
        return self.deserialize(
            stream.read(),
            typed=typed,
            expand_environment=expand_environment,
        )

    # ==========================================================
    # Batch API
    # ==========================================================

    def serialize_many(
        self,
        objects: Iterable[Mapping[str, Any]],
    ) -> list[str]:
        return [
            self.serialize(item)
            for item in objects
        ]

    def deserialize_many(
        self,
        objects: Iterable[str | bytes],
        *,
        typed: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            self.deserialize(
                item,
                typed=typed,
            )
            for item in objects
        ]

    # ==========================================================
    # Compression
    # ==========================================================

    def serialize_compressed(
        self,
        value: Mapping[str, Any],
    ) -> bytes:
        return gzip.compress(
            self.serialize(value).encode(
                self._encoding
            )
        )

    def deserialize_compressed(
        self,
        data: bytes,
        *,
        typed: bool = False,
    ) -> dict[str, Any]:
        try:
            return self.deserialize(
                gzip.decompress(data),
                typed=typed,
            )
        except Exception as exc:
            raise DeserializationError(
                str(exc)
            ) from exc

    # ==========================================================
    # Async API
    # ==========================================================

    async def serialize_async(
        self,
        value: Mapping[str, Any],
    ) -> str:
        return await asyncio.to_thread(
            self.serialize,
            value,
        )

    async def deserialize_async(
        self,
        data: str | bytes,
        *,
        typed: bool = False,
        expand_environment: bool = False,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.deserialize,
            data,
            typed=typed,
            expand_environment=expand_environment,
        )

    async def serialize_to_file_async(
        self,
        value: Mapping[str, Any],
        path: str | Path,
    ) -> Path:
        return await asyncio.to_thread(
            self.serialize_to_file,
            value,
            path,
        )

    async def deserialize_from_file_async(
        self,
        path: str | Path,
        *,
        typed: bool = False,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.deserialize_from_file,
            path,
            typed=typed,
        )

    # ==========================================================
    # Cache
    # ==========================================================

    def _cache_key(
        self,
        value: Mapping[str, Any],
    ) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            default=str,
            ensure_ascii=False,
        )

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def cache_entries(self) -> int:
        with self._lock:
            return len(self._cache)

    def serialize_cached(
        self,
        value: Mapping[str, Any],
    ) -> str:
        if self._cache_size == 0:
            return self.serialize(value)

        key = self._cache_key(value)

        with self._lock:
            if key in self._cache:
                self._cache_hits += 1
                self._cache.move_to_end(key)
                return self._cache[key]

            self._cache_misses += 1

        result = self.serialize(value)

        with self._lock:
            self._cache[key] = result
            self._cache.move_to_end(key)

            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

        return result

    # ==========================================================
    # Metrics
    # ==========================================================

    @property
    def serialization_count(self) -> int:
        return self._serialization_count

    @property
    def deserialization_count(self) -> int:
        return self._deserialization_count

    @property
    def serialization_time(self) -> float:
        return self._serialization_time

    @property
    def deserialization_time(self) -> float:
        return self._deserialization_time

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    @property
    def cache_misses(self) -> int:
        return self._cache_misses

    @property
    def bytes_serialized(self) -> int:
        return self._bytes_serialized

    @property
    def bytes_deserialized(self) -> int:
        return self._bytes_deserialized

    @property
    def average_serialization_time(self) -> float:
        if not self._serialization_count:
            return 0.0

        return (
            self._serialization_time
            / self._serialization_count
        )

    @property
    def average_deserialization_time(self) -> float:
        if not self._deserialization_count:
            return 0.0

        return (
            self._deserialization_time
            / self._deserialization_count
        )

    def statistics(self) -> dict[str, Any]:
        return {
            "serialized":
                self.serialization_count,
            "deserialized":
                self.deserialization_count,
            "serialization_time":
                self.serialization_time,
            "deserialization_time":
                self.deserialization_time,
            "average_serialization_time":
                self.average_serialization_time,
            "average_deserialization_time":
                self.average_deserialization_time,
            "cache_hits":
                self.cache_hits,
            "cache_misses":
                self.cache_misses,
            "bytes_serialized":
                self.bytes_serialized,
            "bytes_deserialized":
                self.bytes_deserialized,
        }

    def performance(self) -> dict[str, float]:
        return {
            "serialization_rate":
                self._rate(
                    self.serialization_count,
                    self.serialization_time,
                ),
            "deserialization_rate":
                self._rate(
                    self.deserialization_count,
                    self.deserialization_time,
                ),
        }

    @staticmethod
    def _rate(
        count: int,
        duration: float,
    ) -> float:
        if duration <= 0:
            return 0.0

        return count / duration

    def reset_metrics(self) -> None:
        self._serialization_count = 0
        self._deserialization_count = 0
        self._serialization_time = 0.0
        self._deserialization_time = 0.0
        self._bytes_serialized = 0
        self._bytes_deserialized = 0

    # ==========================================================
    # Runtime
    # ==========================================================

    def runtime_information(self) -> dict[str, Any]:
        return {
            "codec": self.name,
            "format": self.format,
            "version": VERSION,
            "encoding": self.encoding,
            "configuration":
                self.configuration(),
            "statistics":
                self.statistics(),
        }

    def runtime_summary(self) -> dict[str, Any]:
        return {
            "codec": self.name,
            "format": self.format,
            "version": VERSION,
            "healthy": self.health(),
            "cache_entries":
                self.cache_entries(),
            "statistics":
                self.statistics(),
        }

    def diagnostics(self) -> dict[str, Any]:
        return {
            "healthy": self.health(),
            "runtime":
                self.runtime_information(),
            "performance":
                self.performance(),
            "cache_entries":
                self.cache_entries(),
        }

    def health(self) -> bool:
        return self.self_test()

    # ==========================================================
    # Registry
    # ==========================================================

    def register(self, registry: Any) -> None:
        registry.register(self)

    def unregister(self, registry: Any) -> None:
        registry.unregister(self.name)

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def initialize(self) -> None:
        with self._lock:
            self._cache = OrderedDict()
            self.reset_metrics()

    def reset(self) -> None:
        self.reset_metrics()
        self.clear_cache()

    def shutdown(self) -> None:
        self.reset()

    def dispose(self) -> None:
        self.shutdown()

    def clone(self) -> DotenvCodec:
        return DotenvCodec(
            encoding=self._encoding,
            cache_size=self._cache_size,
            export_prefix=self._export_prefix,
            sort_keys=self._sort_keys,
            space_around_equals=(
                self._space_around_equals
            ),
            quote_values=self._quote_values,
        )

    def export_runtime(self) -> dict[str, Any]:
        return {
            "runtime":
                self.runtime_information(),
            "statistics":
                self.statistics(),
            "performance":
                self.performance(),
            "diagnostics":
                self.diagnostics(),
        }

    def import_runtime(
        self,
        state: Mapping[str, Any],
    ) -> None:
        if not isinstance(state, Mapping):
            return

    # ==========================================================
    # Format helpers
    # ==========================================================

    @staticmethod
    def file_extension() -> str:
        return ".env"

    @staticmethod
    def supported_extensions() -> tuple[str, ...]:
        return (
            ".env",
            ".env.local",
            ".env.dev",
            ".env.development",
            ".env.test",
            ".env.production",
        )

    @staticmethod
    def detect_format(
        filename: str,
    ) -> str:
        name = Path(filename).name.lower()

        if (
            name == ".env"
            or name.startswith(".env.")
        ):
            return "dotenv"

        return "dotenv"

    # ==========================================================
    # Prefix helpers
    # ==========================================================

    def filter_prefix(
        self,
        mapping: Mapping[str, Any],
        prefix: str,
    ) -> dict[str, Any]:
        prefix = str(prefix)

        return {
            str(key): value
            for key, value in mapping.items()
            if str(key).startswith(prefix)
        }

    def strip_prefix(
        self,
        mapping: Mapping[str, Any],
        prefix: str,
    ) -> dict[str, Any]:
        prefix = str(prefix)

        return {
            str(key)[len(prefix):]: value
            for key, value in mapping.items()
            if str(key).startswith(prefix)
        }

    # ==========================================================
    # Merge
    # ==========================================================

    def merge(
        self,
        *mappings: Mapping[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for mapping in mappings:
            if not isinstance(mapping, Mapping):
                raise TypeError(
                    "merge expects mappings"
                )

            for key, value in mapping.items():
                result[self.normalize_key(key)] = value

        return result

    # ==========================================================
    # Environment Diff
    # ==========================================================

    def diff(
        self,
        left: Mapping[str, Any],
        right: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        left_keys = set(
            map(str, left.keys())
        )
        right_keys = set(
            map(str, right.keys())
        )

        added = {
            key: right[key]
            for key in right_keys - left_keys
        }

        removed = {
            key: left[key]
            for key in left_keys - right_keys
        }

        changed = {
            key: {
                "old": left[key],
                "new": right[key],
            }
            for key in left_keys & right_keys
            if left[key] != right[key]
        }

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
        }

    # ==========================================================
    # Schema
    # ==========================================================

    def schema_summary(
        self,
        mapping: Mapping[str, Any],
    ) -> dict[str, Any]:
        keys = [
            self.normalize_key(key)
            for key in mapping.keys()
        ]

        return {
            "key_count": len(keys),
            "keys": keys,
            "nullable": [
                key
                for key, value in mapping.items()
                if value is None
            ],
            "typed_values": {
                key: type(value).__name__
                for key, value in mapping.items()
            },
        }

    # ==========================================================
    # Self Test
    # ==========================================================

    def self_test(self) -> bool:
        sample = {
            "APP_NAME": "AURA",
            "APP_PORT": 8080,
            "APP_DEBUG": True,
            "APP_MESSAGE": "hello world",
            "APP_ITEMS": ["one", "two"],
        }

        try:
            encoded = self.serialize(sample)
            decoded = self.deserialize(
                encoded,
                typed=True,
            )

            if decoded != sample:
                return False

            compressed = self.serialize_compressed(
                sample
            )

            restored = self.deserialize_compressed(
                compressed,
                typed=True,
            )

            return restored == sample

        except Exception:
            return False

    # ==========================================================
    # Representation
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"format='{self.format}', "
            f"encoding='{self._encoding}')"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DotenvCodec):
            return False

        return (
            self.format == other.format
            and self.configuration()
            == other.configuration()
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.format,
                self._encoding,
            )
        )


dotenv_codec = DotenvCodec()


__all__ = [
    "DotenvCodec",
    "dotenv_codec",
]