"""Reflection models and improvement signals."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.ids import AgentId, ExecutionId, GoalId

__all__ = ["ReflectionTarget", "ReflectionSeverity", "ImprovementSignal", "Reflection"]


class ReflectionTarget(enum.Enum):
    """What aspect of behavior a reflection is analyzing."""

    OUTCOME = "outcome"
    DECISION = "decision"
    PLAN = "plan"
    BEHAVIOR = "behavior"
    FAILURE = "failure"
    EFFICIENCY = "efficiency"
    DEVIATION = "deviation"


class ReflectionSeverity(enum.IntEnum):
    """How much a reflection signal matters."""

    INFO = 0
    SUGGESTION = 1
    WARNING = 2
    CRITICAL = 3


@dataclass(frozen=True)
class ImprovementSignal:
    """A structured, validated improvement signal.

    ``signal_type`` is constrained to a small vocabulary of *safe* learning
    targets (e.g. ``strategy.improvement``, ``action.preference``,
    ``memory.consolidation``). Signals that would touch safety policies,
    permission policies, or the constitution are *refused* by design.
    """

    signal_type: str
    target: str
    suggestion: str
    severity: ReflectionSeverity = ReflectionSeverity.SUGGESTION
    evidence: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_safety_relevant(self) -> bool:
        """True when learning this signal must NOT happen automatically."""
        forbidden_prefix = ("safety.", "permission.", "constitution.", "policy.")
        return self.signal_type.startswith(forbidden_prefix)


@dataclass(frozen=True)
class Reflection:
    """A complete reflection over one execution."""

    execution_id: ExecutionId
    agent_id: AgentId
    goal_id: GoalId | None
    targets: list[ReflectionTarget]
    summary: str
    signals: list[ImprovementSignal]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
