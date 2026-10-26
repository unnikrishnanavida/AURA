"""Execution request models: the action being requested and its inputs.

World state and action inputs are strictly separated: ``inputs`` are values
for the action's parameters, never implicit world-state variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from aura_agent.contracts.ids import ActionId, AgentId, ExecutionId, GoalId

__all__ = ["ExecutionRequest"]


@dataclass(frozen=True)
class ExecutionRequest:
    """A request to execute a single action."""

    action_id: ActionId
    tool_name: str
    capability: str
    agent_id: AgentId
    goal_id: GoalId | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    execution_id: ExecutionId | None = None
    idempotency_key: str | None = None

    def with_execution_id(self, execution_id: ExecutionId) -> ExecutionRequest:
        return replace(self, execution_id=execution_id)
