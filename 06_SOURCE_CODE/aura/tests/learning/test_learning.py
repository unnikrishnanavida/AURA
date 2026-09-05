"""Learning domain tests: validated signals, safety authorization, rollback, versioning."""

from __future__ import annotations

from uuid import uuid4

from aura.learning.engine import LearningEngine
from aura.learning.gate import SignalValidator
from aura.learning.models import LearningSignal, SignalStatus


def make_signal(*, evidence_count: int = 2, safety_relevant: bool = False, authorized: bool = False) -> LearningSignal:
    return LearningSignal(
        id=f"sig-{uuid4().hex[:8]}",
        kind="strategy_improvement",
        content="increase exploration rate",
        evidence=[{"score": 0.9}] * evidence_count,
        safety_relevant=safety_relevant,
        authorized=authorized,
    )


def test_signal_rejected_without_evidence() -> None:
    engine = LearningEngine()
    result = engine.submit(make_signal(evidence_count=0))
    assert not result.applied
    assert result.signal.status is SignalStatus.REJECTED
    assert "insufficient evidence" in result.outcome.reason


def test_signal_rejected_with_low_score() -> None:
    validator = SignalValidator(min_evidence_score=0.7)
    engine = LearningEngine(validator=validator)
    signal = LearningSignal.create(kind="x", content="y", evidence=[{"score": 0.1}])
    result = engine.submit(signal)
    assert not result.applied


def test_signal_applied_when_validated() -> None:
    engine = LearningEngine()
    result = engine.submit(make_signal(evidence_count=2))
    assert result.applied
    assert result.change is not None
    assert result.change.ref


def test_safety_relevant_blocked_without_authorization() -> None:
    engine = LearningEngine()
    result = engine.submit(make_signal(evidence_count=2, safety_relevant=True, authorized=False))
    assert not result.applied
    assert "authorization" in result.outcome.reason


def test_safety_relevant_applies_with_authorization() -> None:
    engine = LearningEngine()
    result = engine.approve_and_apply(make_signal(evidence_count=2, safety_relevant=True, authorized=False))
    assert result.applied


def test_rollback() -> None:
    engine = LearningEngine()
    result = engine.submit(make_signal(evidence_count=2))
    assert result.applied
    rolled_back = engine.rollback(result.change.ref)  # type: ignore[arg-type]
    assert rolled_back.ref == result.change.ref  # type: ignore[union-attr]


def test_registry_versions_changes() -> None:
    engine = LearningEngine()
    r1 = engine.submit(make_signal(evidence_count=2))
    r2 = engine.submit(make_signal(evidence_count=2))
    assert r1.change is not None and r2.change is not None
    assert r1.change.ref != r2.change.ref


def test_rejected_signal_status_marker() -> None:
    validator = SignalValidator(min_evidence_count=3)
    engine = LearningEngine(validator=validator)
    result = engine.submit(make_signal(evidence_count=1))
    assert result.signal.status is SignalStatus.REJECTED