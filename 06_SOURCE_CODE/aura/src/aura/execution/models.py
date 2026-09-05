"""Execution domain models.

WorldState is the observable world; ActionInputs are the arguments to one
action. They are distinct by design: an action never reads its inputs from the
world and never writes the world implicitly; effects are declared.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aura.foundation.cancellation import CancellationToken
from aura.foundation.ids import ExecutionId, ToolCallId


@dataclass(frozen=True, slots=True)
class WorldState:
    """Immutable snapshot of observable world state."""

    values: dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.values

    def update(self, **changes: Any) -> WorldState:
        merged = dict(self.values)
        merged.update(changes)
        return WorldState(values=merged)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class ActionInputs:
    """Arguments supplied to an action. Distinct from world state."""

    values: dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Outcome of one action execution (or its recorded replay)."""

    ok: bool
    tool_call_id: ToolCallId
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    execution_id: ExecutionId | None = None
    replayed: bool = False
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tool_call_id": str(self.tool_call_id),
            "output": self.output,
            "error": self.error,
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "replayed": self.replayed,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Declares one executable action: capability, pre/post conditions,
    effects, timeout, retry behavior, and idempotency."""

    name: str
    capability: str
    handler: Callable[[ActionInputs, CancellationToken], ActionResult]
    risk: float = 0.0
    timeout_seconds: float = 30.0
    idempotent: bool = False
    preconditions: tuple[str, ...] = ()
    expected_effects: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    max_retries: int = 0
    declare_world_changes: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.capability:
            raise ValueError("action name and capability must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


def make_result(
    *,
    ok: bool,
    output: dict[str, Any] | None = None,
    error: str = "",
    execution_id: ExecutionId | None = None,
    replayed: bool = False,
) -> ActionResult:
    return ActionResult(
        ok=ok,
        tool_call_id=ToolCallId.new(),
        output=output or {},
        error=error,
        execution_id=execution_id,
        replayed=replayed,
    )


__all__ = ["ActionResult", "ActionInputs", "ActionSpec", "WorldState", "make_result"]