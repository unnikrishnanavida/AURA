"""Strategy evaluation for reflected episodes.

A strategy is judged on whether the selected action was appropriate for the
goal, whether it honored assumptions, and whether a better alternative was
available. The evaluator is a pure analysis; it never changes the plan or the
system.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_reflection.models.reflection_request import OutcomeKind, ReflectionRequest
from aura_reflection.models.reflection_result import AnalysisFinding


@dataclass(frozen=True)
class StrategyAssessment:
    appropriate: bool
    rationale: str
    alternative: str | None = None

    def to_finding(self) -> AnalysisFinding:
        return AnalysisFinding(
            category="strategy_evaluation",
            label="appropriate" if self.appropriate else "suboptimal",
            detail=self.rationale,
        )


class StrategyEvaluator:
    """Evaluates whether the chosen strategy was appropriate."""

    def evaluate(self, request: ReflectionRequest) -> StrategyAssessment:
        out = request.outcome
        if request.kind is OutcomeKind.SUCCESS:
            return StrategyAssessment(
                appropriate=True,
                rationale=f"action {out.action!r} achieved goal {out.goal!r}",
                alternative=None,
            )
        if request.kind is OutcomeKind.FAILURE:
            if out.expected_result and out.actual_result and out.expected_result != out.actual_result:
                return StrategyAssessment(
                    appropriate=False,
                    rationale="strategy did not produce the expected result; preconditions or "
                    f"assumptions for {out.action!r} were not validated",
                    alternative="decompose the action into smaller precondition-checked steps",
                )
            return StrategyAssessment(
                appropriate=False,
                rationale=f"strategy {out.action!r} failed without a usable alternative",
                alternative="introduce a fallback strategy for transient failures",
            )
        return StrategyAssessment(
            appropriate=False,
            rationale="outcome is partial or unknown; strategy cannot be validated as appropriate",
            alternative="define measurable success criteria before executing",
        )