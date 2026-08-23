"""Delegation domain models."""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import AgentId, GoalId

__all__ = ["DelegatedTask", "TaskStatus", "Proposal", "TaskRequirements"]


class TaskStatus(enum.Enum):
    """Lifecycle of a delegated task."""

    PENDING = "pending"
    PROPOSED = "proposed"
    AGREED = "agreed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskRequirements:
    """The capabilities and constraints a delegated task needs."""

    required_capabilities: tuple[str, ...]
    description: str = ""
    deadline_s: float | None = None
    max_cost: float | None = None


@dataclass(frozen=True)
class DelegatedTask:
    """A task delegated by an orchestrator to a worker."""

    task_id: str
    delegator: AgentId
    requirements: TaskRequirements
    status: TaskStatus = TaskStatus.PENDING
    worker: AgentId | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Proposal:
    """A worker's proposal to take on a task."""

    task_id: str
    worker: AgentId
    terms: dict[str, Any] = field(default_factory=dict)
    reliability: float = 0.0
    proposal_id: str = ""

    def __post_init__(self) -> None:
        if not self.proposal_id:
            content = json.dumps(self.terms, sort_keys=True) if self.terms else ""
            digest = hashlib.sha256(content.encode()).hexdigest()[:8]
            object.__setattr__(self, "proposal_id", f"prop-{self.task_id}-{digest}")