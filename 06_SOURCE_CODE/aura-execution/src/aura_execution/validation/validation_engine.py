"""Validation engine: verifies execution results against declared effects."""

from __future__ import annotations

from typing import Any

from aura_execution.validation.results.result_validator import ResultValidator


class ValidationEngine:
    """Checks that the observed state matches the action's declared effects."""

    def __init__(self, validator: ResultValidator | None = None) -> None:
        self.validator = validator or ResultValidator()

    def validate(self, action_result: Any, effects: dict[str, Any], after: dict[str, Any]) -> tuple[bool, str]:
        ok_flag, mismatches = self.validator.validate(action_result, effects, after)
        if ok_flag:
            return True, ""
        return False, f"expected state mismatch: {mismatches}"


__all__ = ["ValidationEngine"]