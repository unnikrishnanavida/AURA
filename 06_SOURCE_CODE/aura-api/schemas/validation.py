"""Request schema validation for aura-api.

Dependency-light, declarative validators. Invalid requests produce structured
:class:`ValidationError` responses with a machine-readable code rather than
unexpected server errors.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aura_api.core.errors import ValidationError

Validator = Callable[[Any], str | None]


@dataclass(frozen=True)
class FieldSpec:
    """A single required/optional field with validators."""

    name: str
    required: bool = True
    kind: type | tuple[type, ...] | None = None
    validators: tuple[Validator, ...] = ()


def _is_kind(value: Any, kind: type | tuple[type, ...]) -> bool:
    if isinstance(kind, tuple):
        return any(isinstance(value, k) for k in kind)
    if kind is bool:
        return isinstance(value, bool)
    if kind is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, kind)


class RequestValidator:
    """Declarative validator for JSON request bodies."""

    def __init__(self, fields: tuple[FieldSpec, ...], *, allow_extra: bool = False) -> None:
        self.fields = fields
        self.allow_extra = allow_extra

    def validate(self, payload: Any) -> dict[str, Any]:
        """Validate a JSON-decoded body; raises ValidationError on failure."""
        if not isinstance(payload, dict):
            raise ValidationError(
                "request body must be a JSON object",
                code="api.invalid_json",
            )
        if not self.allow_extra:
            unknown = set(payload) - {f.name for f in self.fields}
            if unknown:
                raise ValidationError(
                    f"unknown field(s): {', '.join(sorted(unknown))}",
                    code="api.unknown_field",
                )
        result: dict[str, Any] = {}
        for field_spec in self.fields:
            value = payload.get(field_spec.name)
            if value is None and field_spec.required:
                raise ValidationError(
                    f"field {field_spec.name!r} is required",
                    code="api.missing_field",
                )
            if value is None:
                continue
            if field_spec.kind is not None and not _is_kind(value, field_spec.kind):
                raise ValidationError(
                    f"field {field_spec.name!r} must be of type {field_spec.kind}",
                    code="api.wrong_type",
                )
            for validator in field_spec.validators:
                problem = validator(value)
                if problem is not None:
                    raise ValidationError(
                        f"field {field_spec.name!r}: {problem}",
                        code="api.invalid_field",
                    )
            result[field_spec.name] = value
        return result


def non_empty_string(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    return None


def bounded(minimum: float, maximum: float) -> Validator:
    def check(value: Any) -> str | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "must be a number"
        if number < minimum or number > maximum:
            return f"must be in [{minimum}, {maximum}]"
        return None

    return check


def length_limited(max_length: int) -> Validator:
    def check(value: Any) -> str | None:
        if len(str(value)) > max_length:
            return f"must be at most {max_length} characters"
        return None

    return check


__all__ = ["FieldSpec", "RequestValidator", "bounded", "length_limited", "non_empty_string"]