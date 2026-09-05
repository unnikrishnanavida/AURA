"""Learning loop tests: observe->evaluate->signal->validate->apply->monitor->rollback."""

from __future__ import annotations

from aura.learning.engine import LearningEngine
from aura.learning.loop import (
    ExperienceCollector,
    LearningLoop,
    OutcomeEvaluator,
)
from aura.learning.models import SignalStatus


def test_collector_bounded_per_type() -> None:
    collector = ExperienceCollector(max_per_type=3)
    for _ in range(5):
        collector.add(LearningLoop().observe(event_type="run"))
    assert collector.count("run") == 3
    # only the newest three survive
    assert collector.latest("run")[0].id != collector.latest("run")[-1].id


def test_outcome_evaluator_penalizes_deviations() -> None:
    loop = LearningLoop()
    good = loop.observe(event_type="x", expected={"a": 1.0}, observed={"a": 1.0})
    poor = loop.observe(event_type="x", expected={"a": 1.0}, observed={"a": 0.2}, deviations=("late", "wrong"))
    assert OutcomeEvaluator().score(good).score == 1.0
    assert OutcomeEvaluator().score(poor).score < 0.7


def test_evaluate_and_learn_noop_when_quality_ok() -> None:
    loop = LearningLoop()
    loop.observe(event_type="clean", expected={"success": 1.0}, observed={"success": 1.0})
    assert loop.evaluate_and_learn(event_type="clean") is None


def test_evaluate_and_learn_submits_signal_on_poor_outcome() -> None:
    loop = LearningLoop(learn_threshold=0.9)
    loop.observe(event_type="flaky", expected={"success": 1.0}, observed={"success": 0.0})
    result = loop.evaluate_and_learn(event_type="flaky")
    assert result is not None
    assert result.applied
    assert result.signal.kind == "loop_improvement"
    assert result.signal.status is SignalStatus.APPLIED


def test_evaluate_and_learn_requires_minimum_experiences() -> None:
    loop = LearningLoop(min_experiences=2)
    loop.observe(event_type="solo", expected={"success": 1.0}, observed={"success": 0.0})
    assert loop.evaluate_and_learn(event_type="solo") is None


def test_monitor_detects_regression() -> None:
    loop = LearningLoop()
    loop.record_metric("success_rate", 1.0)
    ok = loop.monitor("success_rate", 0.9)
    assert not ok.regressed
    bad = loop.monitor("success_rate", 0.5)
    assert bad.regressed


def test_rollback_through_loop() -> None:
    loop = LearningLoop(learn_threshold=0.9)
    loop.observe(event_type="t", expected={"success": 1.0}, observed={"success": 0.0})
    result = loop.evaluate_and_learn(event_type="t")
    assert result is not None and result.applied and result.change is not None
    rolled_back = loop.rollback(result.change.ref)
    assert rolled_back.ref == result.change.ref


def test_loop_experiences_fed_to_engine() -> None:
    engine = LearningEngine()
    loop = LearningLoop(engine=engine, learn_threshold=0.9)
    loop.observe(event_type="slow", expected={"latency": 1.0}, observed={"latency": 8.0})
    result = loop.evaluate_and_learn(event_type="slow")
    assert result is not None and result.applied
    # engine registry recorded the change
    assert any(change.ref == result.change.ref for change in engine.registry.history())  # type: ignore[attr-defined]