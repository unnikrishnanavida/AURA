"""Evaluation domain models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

__all__ = ["EvaluationVerdict", "StateExpectation", "EvaluationResult"]


class EvaluationVerdict(enum.Enum):
    """Verdict of comparing expected vs observed state."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    STATE_MISMATCH = "state_mismatch"
    DRIFT = "drift"


@dataclass(frozen=True)
class StateExpectation:
    """An explicit expected value for a world-state path.

    ``path`` is dotted (``filesystem.file_created``); this bridges to the
    goal success-criteria model without duplicating it.
    """

    path: str
    expected: Any | None = None
    must_exist: bool = True

    @property
    def predicate(self) -> str:
        if not self.must_exist:
            return f"{self.path} != {self.expected}"
        return f"{self.path} == {self.expected}"


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of evaluating an observed world state against expectations."""

    verdict: EvaluationVerdict
    expectations: list[StateExpectation]
    mismatches: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)
    goal_progress: float = 0.0
    goal_completed: bool = False
    details: dict[str, Any] = field(default_factory=dict)