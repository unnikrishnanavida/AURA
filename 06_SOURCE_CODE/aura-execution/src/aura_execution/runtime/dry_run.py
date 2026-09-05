"""Dry-run and simulation support for aura-execution.

A dry run exercises the full security pipeline and validates the action but
does NOT invoke the handler (no side effects). Simulation contracts let a
caller supply an explicit simulator; otherwise dispatch is skipped.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class DryRunMode:
    """When enabled, execution validates but never dispatches handlers."""

    enabled: bool = False

    def simulate(self, action: Any, inputs: dict[str, Any], context: Any) -> dict[str, Any]:
        """Return a simulated outcome without invoking the handler."""
        return {
            "dry_run": True,
            "simulated": True,
            "action_id": getattr(action, "action_id", None),
            "inputs": dict(inputs),
            "note": "handler not invoked (dry run)",
        }


class Simulator:
    """Runs an action against an explicit simulation instead of the handler."""

    def __init__(self, fn: Callable[..., Any] | None = None) -> None:
        self._fn = fn

    @property
    def has_simulation(self) -> bool:
        return self._fn is not None

    def simulate(self, action: Any, inputs: dict[str, Any], context: Any) -> Any:
        if self._fn is None:
            return DryRunMode(enabled=True).simulate(action, inputs, context)
        return self._fn(action, inputs, context)


__all__ = ["DryRunMode", "Simulator"]