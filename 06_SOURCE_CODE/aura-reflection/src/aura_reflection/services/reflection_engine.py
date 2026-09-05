"""Reflection engine: turns an action outcome into structured reflective output.

Flow:

    ACTION
      â†’ OUTCOME
      â†’ REFLECTION (failure/success + assumption review)
      â†’ COUNTERFACTUAL ANALYSIS
      â†’ LESSON
      â†’ VALIDATED LEARNING SIGNAL (requires external authorization)

The engine never mutates system behavior, policies, or memory. It only produces
a ReflectionResult whose ``signals`` default to unapproved.
"""
from __future__ import annotations

from ..models.reflection_request import ActionOutcome, OutcomeKind, ReflectionRequest
from ..models.reflection_result import (
    AnalysisFinding,
    Counterfactual,
    ImprovementSignal,
    Lesson,
    ReflectionResult,
    ReviewFinding,
)


def _finding_for(kind: OutcomeKind) -> ReviewFinding:
    mapping = {
        OutcomeKind.SUCCESS: ReviewFinding.SUCCESS,
        OutcomeKind.FAILURE: ReviewFinding.FAILURE,
        OutcomeKind.PARTIAL: ReviewFinding.PARTIAL,
        OutcomeKind.UNKNOWN: ReviewFinding.UNKNOWN,
    }
    return mapping[kind]


class ReflectionEngine:
    """Deterministic, bounded reflective analysis of a single episode."""

    def reflect(self, request: ReflectionRequest) -> ReflectionResult:
        kind = request.kind
        out: ActionOutcome = request.outcome
        analyses: list[AnalysisFinding] = []
        lessons: list[Lesson] = []
        signals: list[ImprovementSignal] = []
        counterfactuals: list[Counterfactual] = []
        can_say_i_dont_know = False
        if kind in (OutcomeKind.FAILURE, OutcomeKind.PARTIAL):
            # Failure analysis: expected vs actual result
            if out.expected_result and out.actual_result:
                analyses.append(
                    AnalysisFinding(
                        category="failure_analysis",
                        label="deviation",
                        detail=(
                            f"expected {out.expected_result!r} but observed "
                            f"{out.actual_result!r}"
                        ),
                    )
                )
                lessons.append(
                    Lesson(
                        category="failure_analysis",
                        summary="actual result deviated from expectation without any "
                        "validated cause",
                        confidence=0.4,
                    )
                )
            if out.error:
                analyses.append(
                    AnalysisFinding(
                        category="failure_analysis",
                        label="error",
                        detail=f"error observed: {out.error}",
                    )
                )
                lessons.append(
                    Lesson(
                        category="failure_analysis",
                        summary=f"failed with error: {out.error}",
                        confidence=0.6,
                    )
                )

            # Assumption review: did an assumption break?
            if out.assumptions:
                for assumption in out.assumptions:
                    analyses.append(
                        AnalysisFinding(
                            category="assumption_review",
                            label="unverified_assumption",
                            detail=(
                                "assumption was held without runtime verification: "
                                f"{assumption}"
                            ),
                        )
                    )
                lessons.append(
                    Lesson(
                        category="assumption_review",
                        summary=(
                            "execution depended on unverified assumptions which may "
                            "have contributed to failure"
                        ),
                        confidence=0.5,
                    )
                )
                signals.append(
                    ImprovementSignal(
                        lesson=lessons[-1],
                        proposed_action=(
                            "add precondition validation for assumptions before execution"
                        ),
                    )
                )

            # Counterfactual analysis: what could have worked differently?
            if out.actual_result and out.expected_result and out.actual_result != out.expected_result:
                counterfactuals.append(
                    Counterfactual(
                        alternative_action="verify preconditions before acting",
                        expected_improvement="avoid execution when preconditions are unmet",
                        would_change_outcome=True,
                    )
                )
                analyses.append(
                    AnalysisFinding(
                        category="counterfactual",
                        label="precondition_check",
                        detail="verifying preconditions before execution could have "
                        "prevented the deviation",
                    )
                )
            elif out.error:
                counterfactuals.append(
                    Counterfactual(
                        alternative_action="retry with a fallback strategy",
                        expected_improvement="survive transient errors",
                        would_change_outcome=True,
                    )
                )
            else:
                can_say_i_dont_know = True

        elif kind is OutcomeKind.SUCCESS:
            analyses.append(
                AnalysisFinding(
                    category="outcome_evaluation",
                    label="success",
                    detail=f"goal {out.goal!r} achieved by action {out.action!r}",
                )
            )
            lessons.append(
                Lesson(
                    category="outcome_evaluation",
                    summary="the chosen action achieved its goal",
                    confidence=0.7,
                )
            )
            signals.append(
                ImprovementSignal(
                    lesson=lessons[-1],
                    proposed_action="retain this action pattern for similar goals",
                )
            )

        if can_say_i_dont_know and not lessons:
            lessons.append(
                Lesson(
                    category="uncertainty",
                    summary="insufficient information to extract a reliable lesson",
                    confidence=0.0,
                )
            )

        return ReflectionResult(
            request=request,
            finding=_finding_for(kind),
            analyses=analyses,
            lessons=lessons,
            signals=signals,
            counterfactuals=counterfactuals,
            can_say_i_dont_know=can_say_i_dont_know,
        )
