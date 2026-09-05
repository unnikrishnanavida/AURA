"""Unit tests for the evidence gate and reflection orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_reflection import EvidenceGate, ReflectionEngine, ReflectionOrchestrator
from aura_reflection.services.reflection_gate import UnauthorizedMutationError
from aura_reflection.validation.evidence_gate import EvidenceVerdict
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


def test_evidence_gate_passes_failure_episode():
    gate = EvidenceGate()
    result = ReflectionEngine().reflect(_req())
    assert gate.validate(result).verdict is EvidenceVerdict.SUFFICIENT


def test_evidence_gate_rejects_unknown_episode():
    gate = EvidenceGate()
    result = ReflectionEngine().reflect(
        _req(actual_result=None, error=None, expected_result=None, assumptions=[])
    )
    assert gate.validate(result).verdict is EvidenceVerdict.INSUFFICIENT


def test_orchestrator_signals_start_unapproved():
    orch = ReflectionOrchestrator()
    result = orch.reflect(_req())
    assert result.reflection.signals
    assert result.approved == 0
    assert not result.reflection.approved_signals()


def test_orchestrator_emit_requires_explicit_approver():
    orch = ReflectionOrchestrator()
    result = orch.reflect(_req())
    learning = orch.emit_learning_signal(result, signal_index=0, approver="learning-owner")
    assert learning.approver == "learning-owner"
    assert learning.signal_id
    assert learning.lesson_confidence > 0.0


def test_orchestrator_rejects_out_of_range_signal():
    orch = ReflectionOrchestrator()
    result = orch.reflect(_req())
    with pytest.raises(ValueError):
        orch.emit_learning_signal(result, signal_index=99, approver="owner")


def test_orchestrator_never_approves_without_emit():
    """Even a fully orchestrated pass leaves signals unapproved."""
    orch = ReflectionOrchestrator()
    result = orch.reflect(_req())
    for signal in result.reflection.signals:
        assert signal.approved is False