"""Recovery request/decision models.

Recovery is a *decision* subsystem: given a classified failure, the recovery
engine produces one authoritative strategy. It never executes the strategy
itself; the cognitive loop executes it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.ids import ExecutionId, GoalId
from aura_agent.execution_bridge.responses.execution_result import FailureClass

__all__ = [
    "FailureClass",  # re-exported for convenience
    "RecoveryStrategy",
    "RetryPolicy",
    "RecoveryRequest",
    "RecoveryDecision",
]


class RecoveryStrategy(enum.Enum):
    """The exhaustive set of recovery strategies.

    Exactly one is chosen by the recovery engine; the loop executes it.
    """

    RETRY = "retry"
    FALLBACK = "fallback"
    COMPENSATE = "compensate"
    ROLLBACK = "rollback"
    REPLAN = "replan"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry configuration.

    ``max_retries`` and ``max_total_seconds`` bound retries; ``backoff_s`` is
    a constant base backoff (jitter is deliberately not applied so recovery
    stays deterministic in tests).
    """

    max_retries: int = 2
    backoff_s: float = 0.0
    max_total_seconds: float = float("inf")

    def validate(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries may not be negative")
        if self.backoff_s < 0:
            raise ValueError("backoff_s may not be negative")


@dataclass(frozen=True)
class RecoveryRequest:
    """Everything the recovery engine needs to decide."""

    execution_id: ExecutionId
    goal_id: GoalId | None
    tool_name: str
    failure_class: FailureClass
    attempts: int
    error: str = ""
    retry_policy: RetryPolicy = RetryPolicy()
    fallback_tool: str | None = None
    budget_remaining: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RecoveryDecision:
    """The single authoritative recovery verdict."""

    execution_id: ExecutionId
    strategy: RecoveryStrategy
    reason: str
    retry_after_s: float = 0.0
    attempts: int = 0
    should_retry: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
