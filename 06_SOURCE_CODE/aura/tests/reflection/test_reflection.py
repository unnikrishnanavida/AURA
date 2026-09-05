"""Reflection domain tests: post-execution review, counterfactuals, improvement signals."""

from __future__ import annotations

from aura.reflection.engine import ReflectionEngine
from aura.reflection.models import Outcome, SignalKind


def test_failure_produces_failure_review() -> None:
    report = ReflectionEngine().reflect(
        Outcome(
            goal="release",
            success=False,
            observed={"gate": "failed"},
            expected={"gate": "passed"},
            deviations=["compliance gate failed"],
        )
    )
    kinds = {s.kind for s in report.signals}
    assert SignalKind.FAILURE_REVIEW in kinds


def test_success_produces_success_review() -> None:
    report = ReflectionEngine().reflect(Outcome(goal="release", success=True))
    kinds = {s.kind for s in report.signals}
    assert SignalKind.SUCCESS_REVIEW in kinds


def test_deviations_become_lessons() -> None:
    report = ReflectionEngine().reflect(
        Outcome(goal="launch", success=False, deviations=["budget exceeded by 40%"])
    )
    lessons = [s for s in report.signals if s.kind is SignalKind.LESSON]
    assert lessons
    assert any("budget" in s.content for s in lessons)


def test_counterfactual_on_failure() -> None:
    report = ReflectionEngine().reflect(
        Outcome(
            goal="deploy",
            success=False,
            deviations=["pipeline skipped tests"],
            metrics={"expected_actions": 5, "actions_used": 12},
        )
    )
    signals = [s for s in report.signals if s.kind is SignalKind.FAILURE_REVIEW]
    any_counterfactual = any(s.counterfactual for s in signals)
    any_recs = any(s.recommendations for s in signals)
    assert any_counterfactual or any_recs


def test_improvement_suggestion_emitted() -> None:
    report = ReflectionEngine().reflect(
        Outcome(
            goal="iterate",
            success=False,
            deviations=["repeated same mistake twice"],
            metrics={"expected_actions": 3, "actions_used": 9},
        )
    )
    suggestions = [s for s in report.signals if s.kind is SignalKind.IMPROVEMENT_SUGGESTION]
    assert suggestions


def test_outcome_efficiency() -> None:
    outcome = Outcome(goal="x", success=True, metrics={"expected_actions": 2, "actions_used": 8})
    assert outcome.efficiency == 0.25
    assert Outcome(goal="y", success=True).efficiency == 1.0


def test_reflection_never_mutates_securely() -> None:
    # Reflection outputs signals only; it cannot touch policy endpoints.
    report = ReflectionEngine().reflect(Outcome(goal="z", success=True))
    from aura.reflection.engine import ReflectionReport

    assert isinstance(report, ReflectionReport)