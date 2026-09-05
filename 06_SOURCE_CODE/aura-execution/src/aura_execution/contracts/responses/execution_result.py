"""Execution-level result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_execution.contracts.responses.execution_status import ExecutionStatus


@dataclass
class ExecutionResult:
    """The result of executing an action through the orchestrator."""

    execution_id: str
    status: ExecutionStatus
    result: Any = None
    reason: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status is ExecutionStatus.SUCCEEDED


__all__ = ["ExecutionResult"]