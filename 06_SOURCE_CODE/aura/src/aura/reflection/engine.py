"""Reflection engine.

Post-execution review: why it succeeded or failed, which assumptions were
wrong, what should change next time, and counterfactual analysis of
alternative actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.reflection.models import Outcome, ReflectionSignal, SignalKind


@dataclass
class ReflectionReport:
    goal: str
    signals: list[ReflectionSignal] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "goal": self.goal,
            "summary": self.summary,
            "signals": [s.to_dict() for s in self.signals],
        }


class ReflectionEngine:
    def reflect(self, outcome: Outcome) -> ReflectionReport:
        signals: list[ReflectionSignal] = []
        summary_lines: list[str] = []

        if outcome.success:
            signal_confidence = min(1.0, 0.6 + outcome.efficiency * 0.3)
            signals.append(
                ReflectionSignal(
                    kind=SignalKind.SUCCESS_REVIEW,
                    content=(
                        f"goal {outcome.goal!r} succeeded; efficiency {outcome.efficiency:.2f} "
                        f"with {len(outcome.events_summary)} recorded events"
                    ),
                    confidence=signal_confidence,
                    recommendations=self._success_actions(outcome),
                )
            )
            summary_lines.append(f"success: {outcome.goal}")
        else:
            recommendations = self._change_next_time(outcome)
            signals.append(
                ReflectionSignal(
                    kind=SignalKind.FAILURE_REVIEW,
                    content=self._failure_explanation(outcome),
                    confidence=0.8,
                    counterfactual=self._counterfactuals(outcome),
                    recommendations=recommendations,
                )
            )
            if recommendations:
                signals.append(
                    ReflectionSignal(
                        kind=SignalKind.IMPROVEMENT_SUGGESTION,
                        content=f"improve before retrying goal {outcome.goal!r}: "
                        + "; ".join(recommendations[:2]),
                        confidence=0.7,
                        counterfactual=self._counterfactuals(outcome),
                        recommendations=recommendations,
                    )
                )
            summary_lines.append(f"failure: {outcome.goal}")

        for deviation in outcome.deviations:
            signals.append(
                ReflectionSignal(
                    kind=SignalKind.LESSON,
                    content=f"deviation observed: {deviation}",
                    confidence=0.6,
                )
            )

        for expected, observed in self._mismatched_expectations(outcome):
            signals.append(
                ReflectionSignal(
                    kind=SignalKind.LESSON,
                    content=f"assumption was wrong: expected {expected!r} but observed {observed!r}",
                    confidence=0.7,
                )
            )

        summary = " ".join(summary_lines) or "no outcome data to reflect on"
        return ReflectionReport(goal=outcome.goal, signals=signals, summary=summary)

    @staticmethod
    def _failure_explanation(outcome: Outcome) -> str:
        base = f"goal {outcome.goal!r} failed"
        if outcome.deviations:
            return f"{base}; deviations: {', '.join(outcome.deviations[:3])}"
        if outcome.events_summary:
            return f"{base}; final events: {', '.join(outcome.events_summary[-3:])}"
        return f"{base}; no preconditions were satisfied"

    @staticmethod
    def _counterfactuals(outcome: Outcome) -> tuple[str, ...]:
        if not outcome.deviations:
            return ()
        return tuple(
            f"if the plan had avoided deviation {deviation!r}, the outcome could have differed"
            for deviation in outcome.deviations[:3]
        )

    @staticmethod
    def _change_next_time(outcome: Outcome) -> tuple[str, ...]:
        recommendations: list[str] = []
        if outcome.deviations:
            recommendations.append("tighten precondition validation before execution")
        if not outcome.observed:
            recommendations.append("record observations earlier in the lifecycle")
        return tuple(recommendations or ["validate assumptions before next execution"])

    @staticmethod
    def _success_actions(outcome: Outcome) -> tuple[str, ...]:
        if outcome.events_summary:
            return (f"repeat the successful pattern observed in {outcome.events_summary[:3]}",)
        return ()

    @staticmethod
    def _mismatched_expectations(outcome: Outcome) -> list[tuple[object, object]]:
        mismatches: list[tuple[object, object]] = []
        for key, expected in outcome.expected.items():
            observed = outcome.observed.get(key)
            if observed is None or observed != expected:
                mismatches.append((key, observed))
        return mismatches


__all__ = ["ReflectionEngine", "ReflectionReport"]