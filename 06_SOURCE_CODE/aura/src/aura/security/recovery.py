"""Recovery.

ONE authoritative failure classification and recovery decision authority.
Components ask the single engine instead of deciding recovery themselves,
preventing contradictory recovery decisions across the platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aura.foundation.errors import (
    ApprovalRequiredError,
    AuraError,
    AuraTimeoutError,
    BudgetExhaustedError,
    CapabilityError,
    PermissionDeniedError,
    SafetyDeniedError,
    ValidationError,
)


class FailureKind(StrEnum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    POLICY = "policy"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    STATE_MISMATCH = "state_mismatch"
    UNKNOWN = "unknown"


class Strategy(StrEnum):
    RETRY = "retry"
    FALLBACK = "fallback"
    COMPENSATE = "compensate"
    ROLLBACK = "rollback"
    REPLAN = "replan"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass(frozen=True)
class RecoveryDecision:
    kind: FailureKind
    strategy: Strategy
    reason: str
    retryable: bool = False


class RecoveryClassifier:
    """Maps exceptions to failure kinds."""

    def classify(self, error: BaseException) -> FailureKind:
        if isinstance(error, (CapabilityError, PermissionDeniedError, SafetyDeniedError, ApprovalRequiredError)):
            return FailureKind.POLICY
        if isinstance(error, AuraTimeoutError):
            return FailureKind.TIMEOUT
        if isinstance(error, BudgetExhaustedError):
            return FailureKind.RESOURCE
        if isinstance(error, ValidationError):
            return FailureKind.VALIDATION
        if isinstance(error, AuraError):
            return FailureKind.TRANSIENT
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return FailureKind.TRANSIENT
        return FailureKind.UNKNOWN


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    max_backoff_seconds: float = 8.0


class RecoveryEngine:
    """Single authority translating failure kinds into recovery strategies."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._classifier = RecoveryClassifier()
        self._retry_policy = retry_policy or RetryPolicy()

    def classify(self, error: BaseException) -> FailureKind:
        return self._classifier.classify(error)

    def decide(
        self,
        error: BaseException,
        *,
        attempt: int = 1,
        fallback_available: bool = False,
        compensations_available: bool = False,
    ) -> RecoveryDecision:
        kind = self.classify(error)
        retryable = kind is FailureKind.TRANSIENT and attempt < self._retry_policy.max_attempts
        if kind is FailureKind.TIMEOUT:
            return RecoveryDecision(kind, Strategy.RETRY if attempt < self._retry_policy.max_attempts else Strategy.REPLAN, "timeout handled by bounded retry", retryable=attempt < self._retry_policy.max_attempts)
        if kind is FailureKind.RESOURCE:
            return RecoveryDecision(kind, Strategy.ESCALATE, "resource exhaustion escalates to the operator", False)
        if kind is FailureKind.POLICY:
            return RecoveryDecision(kind, Strategy.ABORT, "hard policy denial must not be retried", False)
        if kind is FailureKind.VALIDATION:
            return RecoveryDecision(kind, Strategy.REPLAN, "invalid request; produce a new valid plan", False)
        if kind is FailureKind.STATE_MISMATCH:
            return RecoveryDecision(kind, Strategy.ROLLBACK, "state mismatch requires rollback", False)
        if kind is FailureKind.TRANSIENT and retryable:
            return RecoveryDecision(kind, Strategy.RETRY, "transient failure; bounded retry", True)
        if fallback_available:
            return RecoveryDecision(kind, Strategy.FALLBACK, "fallback available for permanent failure", False)
        if compensations_available:
            return RecoveryDecision(kind, Strategy.COMPENSATE, "compensate after permanent failure", False)
        return RecoveryDecision(kind, Strategy.ABORT, "no recovery path; abort predictably", False)


__all__ = ["FailureKind", "RecoveryClassifier", "RecoveryDecision", "RecoveryEngine", "RetryPolicy", "Strategy"]