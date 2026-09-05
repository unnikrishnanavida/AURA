"""Unit tests for reflective analysis: mistake detection and strategy evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_reflection.analysis.mistake_detector import MistakeDetector
from aura_reflection.analysis.strategy_evaluator import StrategyEvaluator
from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest


def _req(**kw) -> ReflectionRequest:
    defaults = dict(
        action="run_deploy",
        success=False,
        goal="ship release",
        expected_result="ok",
        actual_result="failed",
        error="timeout",
        assumptions=["network is up"],
    )
    defaults.update(kw)
    return ReflectionRequest(outcome=ActionOutcome(**defaults))


def test_mistake_detector_finds_unverified_assumption():
    mistakes = MistakeDetector().detect(_req())
    assert any(m.kind == "unverified_assumption" for m in mistakes)


def test_mistake_detector_finds_missing_precondition_check():
    mistakes = MistakeDetector().detect(_req())
    assert any(m.kind == "missing_precondition_check" for m in mistakes)


def test_mistake_detector_success_has_no_mistakes():
    mistakes = MistakeDetector().detect(
        _req(success=True, actual_result="ok", error=None, assumptions=[])
    )
    assert mistakes == []


def test_mistake_detector_findings_are_analysis_findings():
    detector = MistakeDetector()
    findings = [m.to_finding() for m in detector.detect(_req())]
    assert all(f.category == "mistake_detection" for f in findings)


def test_strategy_evaluator_success_is_appropriate():
    assessment = StrategyEvaluator().evaluate(
        _req(success=True, actual_result="ok", error=None, assumptions=[])
    )
    assert assessment.appropriate is True


def test_strategy_evaluator_failure_is_suboptimal_with_alternative():
    assessment = StrategyEvaluator().evaluate(_req())
    assert assessment.appropriate is False
    assert assessment.alternative is not None


def test_strategy_evaluator_partial_needs_measurable_criteria():
    assessment = StrategyEvaluator().evaluate(
        _req(success=False, actual_result="partial", error=None, expected_result="ok", assumptions=[])
    )
    assert assessment.appropriate is False