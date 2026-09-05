"""Module-level result validation helper."""

from __future__ import annotations

from typing import Any

from aura_execution.validation.results.expected_state_validator import (
    ExpectedStateValidator,
)
from aura_execution.validation.results.outcome_validator import OutcomeValidator


def validate_result(action_result: Any, effects: dict[str, Any], after: dict[str, Any]) -> tuple[bool, str]:
    """Validate a result against declared effects; returns (ok, detail)."""
    outcome = OutcomeValidator()
    expected = ExpectedStateValidator()
    if not outcome.validate(action_result):
        return False, action_result.error or "action reported failure"
    ok_flag, mismatches = expected.compare(effects, after)
    if not ok_flag:
        return False, f"expected state mismatch: {mismatches}"
    return True, ""


__all__ = ["validate_result"]