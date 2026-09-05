"""Security tests for aura-reflection.

Learning signals must pass validation and authorization boundaries; reflection
must never automatically modify system behavior, policies, or memory; and
sensitive data must not leak through reflection output.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_reflection import ReflectionEngine, ReflectionGate
from aura_reflection.bridges.learning_bridge import LearningSignalBroker
from aura_reflection.bridges.memory_bridge import MemoryBridge
from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest
from aura_reflection.services.reflection_gate import UnauthorizedMutationError


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


def test_unauthorized_automatic_mutation_rejected():
    """Reflection output must never silently alter behavior."""
    gate = ReflectionGate()
    engine = ReflectionEngine()
    result = engine.reflect(_req())
    for signal in result.signals:
        with pytest.raises(UnauthorizedMutationError):
            gate.require_approved(signal)


def test_learning_signal_requires_approver():
    """An approved-looking signal without an approver identity is invalid."""
    gate = ReflectionGate()
    engine = ReflectionEngine()
    result = engine.reflect(_req())
    signal = result.signals[0]
    # forge an approved signal with no approver -> gate must reject
    from aura_reflection.models.reflection_result import ImprovementSignal

    forged = ImprovementSignal(
        lesson=signal.lesson,
        proposed_action=signal.proposed_action,
        approved=True,
        approver=None,
    )
    valid, reason = gate.validate(forged)
    assert not valid
    assert "authorizer" in reason


def test_memory_bridge_never_auto_writes():
    engine = ReflectionEngine()
    result = engine.reflect(_req())
    bridge = MemoryBridge()
    for signal in result.signals:
        with pytest.raises(UnauthorizedMutationError):
            bridge.write_lesson(
                type(
                    "L",
                    (),
                    {
                        "signal_id": "x",
                        "lesson": signal.lesson.summary,
                        "lesson_confidence": signal.lesson.confidence,
                        "proposed_action": signal.proposed_action,
                        "approver": "",
                    },
                )()
            )
    assert bridge.writes == []


def test_sensitive_data_redacted_from_signal():
    """Reflection signals must not propagate secrets in raw form."""
    engine = ReflectionEngine()
    result = engine.reflect(
        _req(error="token sk-abcdef123456 leaked during auth")
    )
    broker = LearningSignalBroker(gate=ReflectionGate())
    approved = ReflectionGate().authorize(result.signals[0], approver="reviewer")
    signal = broker.package(approved)
    redacted = signal.to_dict()
    assert "sk-abcdef123456" not in redacted["lesson"]
    assert "sk-abcdef123456" not in redacted["proposed_action"]


def test_invalid_signal_never_authorized():
    gate = ReflectionGate()
    engine = ReflectionEngine()
    result = engine.reflect(_req())
    # Take the engine signal and zero out its lesson confidence
    from aura_reflection.models.reflection_result import Lesson

    bad = result.signals[0].lesson
    zero_conf = type("Z", (), {"category": bad.category, "summary": bad.summary, "confidence": 0.0})()
    invalid_signal = type(
        "S",
        (),
        {
            "lesson": zero_conf,
            "proposed_action": result.signals[0].proposed_action,
            "approved": False,
            "approver": None,
        },
    )()
    valid, reason = gate.validate(invalid_signal)
    assert not valid
    assert "confidence" in reason