"""Outcome validator: verifies that an action result is a success."""

from __future__ import annotations

from typing import Any


class OutcomeValidator:
    """Checks the success flag of an action result."""

    def validate(self, result: Any) -> bool:
        return bool(getattr(result, "success", False))


__all__ = ["OutcomeValidator"]