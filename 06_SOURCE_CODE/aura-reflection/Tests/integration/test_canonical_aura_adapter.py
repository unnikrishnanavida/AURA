"""Integration tests: aura-reflection bridges to the canonical AURA runtime.

The canonical ``aura`` package is installed as an editable dependency. These
tests prove that reflection output here can be consumed by the canonical
``aura.reflection`` / ``aura.learning`` contracts.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_reflection import ReflectionEngine, ReflectionOrchestrator
from aura_reflection.integrations.aura_canonical import (
    BridgeUnavailable,
    to_canonical_outcome,
    to_canonical_signal,
    to_request,
)
from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest


@pytest.fixture
def canonical_ok():
    try:
        import aura  # noqa: F401
    except ImportError:
        return False
    return True


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


@pytest.mark.skipif("not canonical_ok")
def test_canonical_outcome_round_trip():
    req = _req()
    canonical = to_canonical_outcome(req.outcome)
    assert canonical.goal == "ship release"
    assert canonical.success is False
    back = to_request(canonical)
    assert back.outcome.goal == canonical.goal
    assert back.outcome.success == canonical.success


@pytest.mark.skipif("not canonical_ok")
def test_canonical_engine_can_consume_bridge_outcome():
    from aura.reflection.engine import ReflectionEngine as CanonicalEngine

    req = _req()
    canonical = to_canonical_outcome(req.outcome)
    report = CanonicalEngine().reflect(canonical)
    assert report.goal == "ship release"
    assert report.signals


@pytest.mark.skipif("not canonical_ok")
def test_canonical_signal_from_approved_learning():
    orchestrator = ReflectionOrchestrator()
    orchestrated = orchestrator.reflect(_req())
    learning = orchestrator.emit_learning_signal(orchestrated, signal_index=0, approver="owner")
    canonical_signal = to_canonical_signal(learning)
    assert canonical_signal.confidence == pytest.approx(learning.lesson_confidence)
    assert canonical_signal.recommendations[0] == learning.proposed_action


@pytest.mark.skipif("canonical_ok")
def test_bridge_unavailable_without_canonical():
    with pytest.raises(BridgeUnavailable):
        to_canonical_outcome(ActionOutcome(action="a", success=False, goal="g"))