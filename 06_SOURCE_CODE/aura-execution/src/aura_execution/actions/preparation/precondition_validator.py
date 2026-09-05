"""Precondition validation before an action is dispatched."""

from __future__ import annotations

from typing import Any


def check_preconditions(action: Any, state: dict[str, Any], inputs: dict[str, Any]) -> list[str]:
    """Evaluate declared preconditions against current state + inputs.

    Each precondition is a predicate over ``(state, inputs)``; a falsy result
    records a failure. Unknown/absent preconditions are treated conservatively
    (they fail closed rather than silently passing).
    """
    failures: list[str] = []
    preconditions = action.preconditions or {}
    for name, predicate in preconditions.items():
        try:
            ok_flag = bool(predicate(state, inputs))
        except Exception as exc:  # noqa: BLE001 - a broken predicate must not pass
            ok_flag = False
            failures.append(f"{name}: precondition raised {type(exc).__name__}")
        if not ok_flag:
            failures.append(f"{name}: precondition not satisfied")
    return failures


def require_preconditions(action: Any, state: dict[str, Any], inputs: dict[str, Any]) -> None:
    failures = check_preconditions(action, state, inputs)
    if failures:
        raise ValueError(f"preconditions failed: {failures}")


__all__ = ["check_preconditions", "require_preconditions"]