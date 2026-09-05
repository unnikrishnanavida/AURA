"""Reflection result: structured output of a reflective review.

A reflection result records what happened, why, what lessons were extracted,
and (critically) a set of *candidate* improvement / learning signals that still
require validation and authorization before they may influence behavior.
Reflection NEVER mutates the system directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .reflection_request import ReflectionRequest


class ReviewFinding(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnalysisFinding:
    """One analytical conclusion from the reflection."""

    category: str  # e.g. "failure_analysis", "assumption_review", "counterfactual"
    label: str
    detail: str


@dataclass(frozen=True)
class Lesson:
    """A distilled lesson from an episode."""

    category: str
    summary: str
    confidence: float = 0.5


@dataclass(frozen=True)
class ImprovementSignal:
    """A candidate learning signal.

    ``approved`` defaults to False. Only an explicit authorization boundary
    (see reflection_gate) may set it to True; the engine never does so itself.
    """

    lesson: Lesson
    proposed_action: str
    approved: bool = False
    approver: str | None = None


@dataclass(frozen=True)
class Counterfactual:
    """An alternative action that could plausibly have changed the outcome."""

    alternative_action: str
    expected_improvement: str
    would_change_outcome: bool


@dataclass
class ReflectionResult:
    """Summary of a reflection pass.

    ``signals`` are never auto-approved by the engine; an authorized gate must
    approve them. ``can_say_i_dont_know`` marks episodes where the evidence is
    too weak to extract confident lessons.
    """

    request: ReflectionRequest
    finding: ReviewFinding
    analyses: list[AnalysisFinding] = field(default_factory=list)
    lessons: list[Lesson] = field(default_factory=list)
    signals: list[ImprovementSignal] = field(default_factory=list)
    counterfactuals: list[Counterfactual] = field(default_factory=list)
    can_say_i_dont_know: bool = False

    def approved_signals(self) -> list[ImprovementSignal]:
        return [s for s in self.signals if s.approved]