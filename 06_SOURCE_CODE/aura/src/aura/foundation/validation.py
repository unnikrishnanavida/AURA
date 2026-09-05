"""Deterministic validation helpers used across engines.

The `validators` object gives engines a small composable toolkit. `ensure`
is the fast-path assertion that raises the platform :class:`ValidationError`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aura.foundation.errors import ValidationError


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


class _Validators:
    def not_empty(self, value: Any, *, name: str = "value") -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{name} must be a non-empty string")
        return value

    def in_range(self, value: float, low: float, high: float, *, name: str = "value") -> float:
        if not low <= value <= high:
            raise ValidationError(f"{name} must be in [{low}, {high}], got {value}")
        return value

    def is_number(self, value: Any, *, name: str = "value") -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"{name} must be numeric")
        return float(value)

    def is_instance(self, value: Any, expected: type, *, name: str = "value") -> Any:
        if not isinstance(value, expected):
            raise ValidationError(f"{name} must be of type {expected.__name__}")
        return value

    def belonged_to(self, value: str, allowed: Iterable[str], *, name: str = "value") -> str:
        canon = {str(a) for a in allowed}
        if value not in canon:
            raise ValidationError(f"{name} must be one of {sorted(canon)}, got {value!r}")
        return value

    def identifier(self, value: Any, *, name: str = "id") -> str:
        text = self.not_empty(value, name=name)
        if not (text.isalnum() or "-" in text or "_" in text):
            raise ValidationError(f"{name} contains unsupported characters: {text!r}")
        return text


validators = _Validators()

__all__ = ["ensure", "validators"]