"""Retry policy and failure classification for aura-execution.

Transient failures may be retried; non-retryable (policy, permanent) failures
must NOT be retried. Classification is explicit so the engine never burns
retries on permanent faults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RetryClass(StrEnum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"


@dataclass(frozen=True)
class FailureClassification:
    """Classification of a failure with a reason."""

    retry_class: RetryClass
    reason: str
    mute_patterns: tuple[str, ...] = ()

    @property
    def retryable(self) -> bool:
        return self.retry_class is RetryClass.RETRYABLE


class RetryClassifier:
    """Classifies failures by inspecting the error text."""

    TRANSIENT_HINTS = ("timeout", "tempor", "connection", "transient", "throttl", "rate limit")
    PERMANENT_HINTS = ("denied", "permission", "safety", "forbidden", "not found", "invalid", "unsupported")

    def classify(self, error: Any) -> FailureClassification:
        text = str(error).lower()
        if any(hint in text for hint in self.PERMANENT_HINTS):
            return FailureClassification(RetryClass.NON_RETRYABLE, "permanent failure pattern")
        if any(hint in text for hint in self.TRANSIENT_HINTS):
            return FailureClassification(RetryClass.RETRYABLE, "transient failure pattern")
        return FailureClassification(RetryClass.RETRYABLE, "unclassified; treat as transient")


@dataclass
class RetryPolicy:
    """How many times and with what backoff an action may be retried."""

    max_retries: int = 2
    backoff_seconds: float = 0.01
    classifier: RetryClassifier = field(default_factory=RetryClassifier)

    def should_retry(self, error: Any, attempt: int) -> tuple[bool, str]:
        """Decide whether to retry after ``attempt`` failures.

        Attempt is 0-based (0 = first attempt that already failed). Retries
        are only allowed for retryable classifications and within the budget.
        """
        if attempt >= self.max_retries:
            return False, "retry budget exhausted"
        classification = self.classifier.classify(error)
        if not classification.retryable:
            return False, classification.reason
        return True, classification.reason


__all__ = ["FailureClassification", "RetryClass", "RetryClassifier", "RetryPolicy"]