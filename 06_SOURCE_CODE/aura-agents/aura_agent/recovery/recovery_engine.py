"""Recovery engine: the ONE authoritative recovery decision maker.

Failure classes map deterministically to recovery strategies:

- ``TRANSIENT`` / ``TIMEOUT`` -> ``RETRY`` when retries remain, else ``ABORT``
- ``PERMANENT`` -> ``ABORT`` (no point retrying)
- ``STATE_MISMATCH`` -> ``ROLLBACK`` then ``REPLAN`` when rollback unavailable
- ``RESOURCE`` -> ``ESCALATE`` (budget is a controller decision)
- ``POLICY`` / ``VALIDATION`` -> ``ABORT`` (retrying a denial is harmful)
- ``UNKNOWN`` -> ``REPLAN`` with a single attempt; never blind retry

The engine records its own outcome history so downstream telemetry can count
recovery effectiveness. Retry policy is fully respected; calls to the engine
never bypass ``max_retries``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aura_agent.execution_bridge.responses.execution_result import FailureClass
from aura_agent.recovery.models import (
    RecoveryDecision,
    RecoveryRequest,
    RecoveryStrategy,
)

__all__ = ["RecoveryEngine"]


class RecoveryEngine:
    """Consumes ``RecoveryRequest`` and returns ``RecoveryDecision``."""

    def __init__(self) -> None:
        self._outcomes: list[dict] = []

    def decide(self, request: RecoveryRequest) -> RecoveryDecision:
        strategy, reason, retry_after = self._resolve(request)

        should_retry = strategy is RecoveryStrategy.RETRY
        attempts = request.attempts + 1
        decision = RecoveryDecision(
            execution_id=request.execution_id,
            strategy=strategy,
            reason=reason,
            retry_after_s=retry_after,
            attempts=attempts,
            should_retry=should_retry,
        )
        self._record(request, decision)
        return decision

    def _resolve(self, request: RecoveryRequest) -> tuple[RecoveryStrategy, str, float]:
        # hard classification matrix ----------------------------
        if request.failure_class in (FailureClass.TRANSIENT, FailureClass.TIMEOUT):
            if request.attempts < request.retry_policy.max_retries:
                return (
                    RecoveryStrategy.RETRY,
                    f"transient failure (attempt {request.attempts + 1}); "
                    f"retry budget allows up to {request.retry_policy.max_retries}",
                    request.retry_policy.backoff_s,
                )
            return (
                RecoveryStrategy.ABORT,
                f"retry budget exhausted after {request.attempts} attempts",
                0.0,
            )

        if request.failure_class is FailureClass.PERMANENT:
            return (RecoveryStrategy.ABORT, "permanent failure; retry would be meaningless", 0.0)

        if request.failure_class is FailureClass.STATE_MISMATCH:
            if request.attempts < 1:
                return (
                    RecoveryStrategy.ROLLBACK,
                    "observed state deviated from expected; rolling back before retry",
                    0.0,
                )
            return (RecoveryStrategy.REPLAN, "rollback already attempted; replanning", 0.0)

        if request.failure_class is FailureClass.RESOURCE:
            return (
                RecoveryStrategy.ESCALATE,
                "resource/budget constraint reached; escalate to controller",
                0.0,
            )

        if request.failure_class in (FailureClass.POLICY, FailureClass.VALIDATION):
            return (
                RecoveryStrategy.ABORT,
                f"denied/validation failure ({request.failure_class.value}); retrying is not safe",
                0.0,
            )

        # UNKNOWN
        if request.attempts >= 1:
            return (RecoveryStrategy.ABORT, "unknown failure repeated; aborting", 0.0)
        return (
            RecoveryStrategy.REPLAN,
            "unknown failure; replanning once before aborting",
            0.0,
        )

    # -- observability ----------------------------------------------------------
    def record_outcome(self, decision: RecoveryDecision, *, success: bool) -> None:
        self._outcomes.append(
            {
                "execution_id": str(decision.execution_id),
                "strategy": decision.strategy.value,
                "success": success,
                "at": datetime.now(UTC).isoformat(),
            }
        )

    @property
    def outcomes(self) -> list[dict]:
        return list(self._outcomes)

    def _record(self, request: RecoveryRequest, decision: RecoveryDecision) -> None:
        self._outcomes.append(
            {
                "execution_id": str(request.execution_id),
                "failure_class": request.failure_class.value,
                "strategy": decision.strategy.value,
                "at": datetime.now(UTC).isoformat(),
            }
        )

    def clear(self) -> None:
        self._outcomes.clear()