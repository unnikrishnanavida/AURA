"""Mistake detection for reflected episodes.

Complements the reflection engine by identifying concrete, generalizable
mistake patterns in an action outcome: missing precondition checks, acting
without a fallback, treating assumptions as facts, or rushing to retry after a
transient failure without a reason to expect a different result.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_reflection.models.reflection_request import (
    OutcomeKind,
    ReflectionRequest,
)
from aura_reflection.models.reflection_result import AnalysisFinding


@dataclass(frozen=True)
class Mistake:
    kind: str
    detail: str
    severity: float  # 0..1

    def to_finding(self) -> AnalysisFinding:
        return AnalysisFinding(category="mistake_detection", label=self.kind, detail=self.detail)


class MistakeDetector:
    """Detects named mistake patterns in an action outcome."""

    def detect(self, request: ReflectionRequest) -> list[Mistake]:
        out = request.outcome
        mistakes: list[Mistake] = []
        if request.kind not in (OutcomeKind.FAILURE, OutcomeKind.PARTIAL):
            return mistakes

        if out.assumptions and out.error:
            mistakes.append(
                Mistake(
                    kind="unverified_assumption",
                    detail="execution proceeded on unverified assumption(s) while erroring: "
                    f"{' | '.join(out.assumptions[:3])}",
                    severity=0.7,
                )
            )
        if out.expected_result and out.actual_result and out.expected_result != out.actual_result:
            mistakes.append(
                Mistake(
                    kind="missing_precondition_check",
                    detail="outcome deviated from expectation; preconditions were not validated "
                    "before execution",
                    severity=0.8,
                )
            )
        if out.actual_result is None and out.success is False and out.error is None:
            mistakes.append(
                Mistake(
                    kind="no_observable_outcome",
                    detail="execution ended without any observable result or error; outcome cannot "
                    "be evaluated",
                    severity=0.5,
                )
            )
        return mistakes