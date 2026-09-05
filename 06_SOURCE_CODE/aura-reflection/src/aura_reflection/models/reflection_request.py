"""Reflection request: what triggered a reflective review.

A reflection is requested after some action produced an outcome. The request
carries the action description, the observed outcome, the goal that the action
was meant to advance, and any assumptions the actor held beforehand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


class OutcomeKind(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class ActionOutcome:
    """The observed result of a single executed action."""

    action: str
    success: bool
    goal: str
    expected_result: str | None = None
    actual_result: str | None = None
    execution_id: str | None = None
    assumptions: list[str] = field(default_factory=list)
    error: str | None = None
    occurred_at: datetime = field(default_factory=utcnow)


@dataclass
class ReflectionRequest:
    """Input to the reflection engine."""

    outcome: ActionOutcome
    request_id: str = field(default_factory=lambda: str(uuid4()))
    requested_at: datetime = field(default_factory=utcnow)

    @property
    def kind(self) -> OutcomeKind:
        if self.outcome.error and not self.outcome.success:
            return OutcomeKind.FAILURE
        if self.outcome.success:
            return OutcomeKind.SUCCESS
        return OutcomeKind.PARTIAL if self.outcome.actual_result else OutcomeKind.FAILURE
