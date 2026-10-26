"""Execution result models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import ExecutionId

__all__ = ["ActionResult", "ExecutionResult", "FailureClass"]


class FailureClass(enum.Enum):
    """Classification of execution failures (input to recovery decisioning).

    Exactly one class is authoritative for a failed execution.
    """

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    POLICY = "policy"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    STATE_MISMATCH = "state_mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ActionResult:
    """The outcome of a single action attempt."""

    execution_id: ExecutionId
    action_id: str
    tool_name: str
    success: bool = False
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    failure_class: FailureClass | None = None
    duration_s: float = 0.0
    retried: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    observed_effects: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """The aggregate outcome of an execution attempt, including the action
    result, observation, evaluation, and recovery information."""

    execution_id: ExecutionId
    success: bool
    results: list[ActionResult] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    evaluation: dict[str, Any] = field(default_factory=dict)
    recovery: dict[str, Any] = field(default_factory=dict)
    state: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    @property
    def primary(self) -> ActionResult | None:
        return self.results[-1] if self.results else None
