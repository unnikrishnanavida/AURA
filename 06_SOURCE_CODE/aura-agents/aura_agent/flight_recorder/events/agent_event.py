"""Core agent event model shared by the flight recorder and the execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aura_agent.contracts.ids import AgentId, ExecutionId

__all__ = ["AgentEvent"]


@dataclass(frozen=True)
class AgentEvent:
    """A single structured event in the agent's execution history.

    ``event_id`` is unique per event; ``execution_id`` groups events into a
    trajectory; ``correlation_id`` links related executions. Payload is a
    plain JSON-serializable mapping suitable for the event store.
    """

    event_type: str
    payload: dict[str, Any]
    execution_id: ExecutionId | None = None
    agent_id: AgentId | None = None
    goal_id: str | None = None
    correlation_id: str | None = None
    event_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))