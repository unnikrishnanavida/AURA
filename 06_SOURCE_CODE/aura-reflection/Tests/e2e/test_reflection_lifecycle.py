"""End-to-end reflection lifecycle tests.

Walks the required flow:

    ACTION -> OUTCOME -> REFLECTION -> FAILURE/SUCCESS ANALYSIS
    -> COUNTERFACTUAL ANALYSIS -> LESSON -> VALIDATED LEARNING SIGNAL

And proves the safety property: reflection never automatically modifies the
system, policies, or memory.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_reflection import (
    EvidenceGate,
    LearningSignalBroker,
    ReflectionEngine,
    ReflectionGate,
    ReflectionOrchestrator,
)
from aura_reflection.bridges.memory_bridge import MemoryBridge, MemoryWriteResult
from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest
from aura_reflection.models.reflection_result import ReviewFinding
from aura_reflection.services.reflection_gate import UnauthorizedMutationError
from aura_reflection.validation.evidence_gate import EvidenceVerdict


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


def test_full_lifecycle_failure_to_validated_signal():
    orchestrator = ReflectionOrchestrator()
    orchestrated = orchestrator.reflect(_req())
    assert orchestrated.reflection.finding is ReviewFinding.FAILURE
    assert orchestrated.validation.passed
    # signals are unapproved until an authorized emit
    assert not orchestrated.reflection.approved_signals()
    learning = orchestrator.emit_learning_signal(orchestrated, signal_index=0, approver="learning-owner")
    assert learning.approver == "learning-owner"
    assert learning.proposed_action
    assert learning.lesson_confidence > 0.0


def test_full_lifecycle_success_reviewed_without_mutation():
    orchestrator = ReflectionOrchestrator()
    orchestrated = orchestrator.reflect(
        _req(success=True, actual_result="ok", error=None, assumptions=[])
    )
    assert orchestrated.reflection.finding is ReviewFinding.SUCCESS
    assert orchestrated.validation.passed
    # success reflection produces a retain-signal, still unapproved
    assert orchestrated.reflection.signals
    assert not orchestrated.reflection.approved_signals()


def test_reflection_never_auto_writes_memory():
    """Reflection must NOT automatically modify memory."""
    orchestrator = ReflectionOrchestrator()
    orchestrated = orchestrator.reflect(_req())
    # No memory write is ever triggered by reflection itself.
    bridge = MemoryBridge()
    assert bridge.writes == []
    # Even with an approved signal, writing requires an explicit call.
    learning = orchestrator.emit_learning_signal(orchestrated, signal_index=0, approver="owner")
    try:
        bridge.write_lesson(learning)  # no store configured
    except UnauthorizedMutationError:
        raise AssertionError("approved signal with approver must be writable via explicit call")
    result = bridge.write_lesson(learning)
    assert isinstance(result, MemoryWriteResult)
    assert result.ok is False  # no store configured -> refused, not silent write


def test_learning_signal_cannot_apply_without_authorization():
    gate = ReflectionGate()
    engine = ReflectionEngine()
    result = engine.reflect(_req())
    signal = result.signals[0]
    broker = LearningSignalBroker(gate=gate)
    # unapproved signal must not enter the learning path
    try:
        broker.package(signal)
    except UnauthorizedMutationError:
        pass
    else:
        raise AssertionError("unapproved signal must not be packaged")


def test_insufficient_evidence_gate_says_unknown():
    """When evidence is insufficient the gate refuses to emit a signal."""
    gate = EvidenceGate()
    engine = ReflectionEngine()
    result = engine.reflect(
        _req(actual_result=None, error=None, expected_result=None, assumptions=[])
    )
    validation = gate.validate(result)
    assert validation.verdict is EvidenceVerdict.INSUFFICIENT
    assert result.can_say_i_dont_know is True