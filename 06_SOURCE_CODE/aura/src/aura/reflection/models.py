"""Reflection domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SignalKind(StrEnum):
    SUCCESS_REVIEW = "success_review"
    FAILURE_REVIEW = "failure_review"
    LESSON = "lesson"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"


@dataclass
class Outcome:
    goal: str
    success: bool
    observed: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    deviations: list[str] = field(default_factory=list)
    events_summary: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def efficiency(self) -> float:
        if not self.metrics:
            return 1.0
        if "expected_actions" in self.metrics and "actions_used" in self.metrics:
            expected = max(1, int(self.metrics["expected_actions"]))
            used = max(1, int(self.metrics["actions_used"]))
            return min(1.0, expected / used)
        return 1.0


@dataclass(frozen=True, slots=True)
class ReflectionSignal:
    kind: SignalKind
    content: str
    confidence: float = 0.5
    counterfactual: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "content": self.content,
            "confidence": self.confidence,
            "counterfactual": list(self.counterfactual),
            "recommendations": list(self.recommendations),
        }


__all__ = ["Outcome", "ReflectionSignal", "SignalKind"]