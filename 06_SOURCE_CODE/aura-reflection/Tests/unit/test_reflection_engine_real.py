"""Behavioral tests for the AURA Reflection engine and gate.

These are the preserved behavioral tests from the original flat ``Reflection/``
layout, repointed at the canonical ``aura_reflection`` package.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest
from aura_reflection.models.reflection_result import ImprovementSignal, Lesson, ReviewFinding
from aura_reflection.services.reflection_engine import ReflectionEngine
from aura_reflection.services.reflection_gate import (
    ReflectionGate,
    UnauthorizedMutationError,
    apply_if_authorized,
)


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


def test_engine_reflects_failure() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(_req())
    assert result.finding is ReviewFinding.FAILURE
    assert any(a.category == "failure_analysis" for a in result.analyses)
    assert result.lessons


def test_failed_execution_captures_error() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(_req(error="timeout"))
    assert any("timeout" in a.detail for a in result.analyses)


def test_incorrect_assumption_is_flagged() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(_req(assumptions=["network is up"]))
    assert any(a.category == "assumption_review" for a in result.analyses)
    # the assumption lesson yields an UNapproved signal
    assert result.signals
    assert not result.approved_signals()


def test_poor_strategy_detected_via_counterfactual() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(_req(expected_result="ok", actual_result="degraded"))
    assert any(a.category == "counterfactual" for a in result.analyses)
    assert result.counterfactuals


def test_successful_outcome_reviewed() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(
        _req(success=True, actual_result="ok", error=None, assumptions=[])
    )
    assert result.finding is ReviewFinding.SUCCESS
    assert any(a.category == "outcome_evaluation" for a in result.analyses)


def test_uncertain_outcome_may_say_i_dont_know() -> None:
    eng = ReflectionEngine()
    result = eng.reflect(
        _req(actual_result=None, error=None, expected_result=None, assumptions=[])
    )
    assert result.can_say_i_dont_know
    assert any(l.category == "uncertainty" for l in result.lessons)


def test_signals_require_authorization() -> None:
    gate = ReflectionGate()
    eng = ReflectionEngine()
    result = eng.reflect(_req())
    assert result.signals
    for signal in result.signals:
        assert not signal.approved
        try:
            gate.require_approved(signal)
        except UnauthorizedMutationError:
            pass
        else:
            raise AssertionError("unapproved signal must be rejected")


def test_gate_authorizes_with_identity() -> None:
    gate = ReflectionGate()
    eng = ReflectionEngine()
    result = eng.reflect(_req())
    signal = result.signals[0]
    approved = gate.authorize(signal, approver="policy-reviewer")
    assert approved.approved
    assert approved.approver == "policy-reviewer"
    assert not signal.approved  # original untouched


def test_invalid_signal_rejected() -> None:
    gate = ReflectionGate()
    eng = ReflectionEngine()
    result = eng.reflect(_req())
    # zero-confidence lesson is invalid for acting
    bad = ImprovementSignal(lesson=Lesson("x", "y", confidence=0.0), proposed_action="do x")
    valid, reason = gate.validate(bad)
    assert not valid
    assert "confidence" in reason
    try:
        gate.authorize(bad, "approver")
    except UnauthorizedMutationError:
        pass
    else:
        raise AssertionError("invalid signal must not be authorized")


def test_apply_requires_approved() -> None:
    gate = ReflectionGate()
    eng = ReflectionEngine()
    result = eng.reflect(_req())
    signal = result.signals[0]
    # No approver supplied -> must not apply.
    try:
        apply_if_authorized(gate, signal)
    except UnauthorizedMutationError:
        pass
    else:
        raise AssertionError("unapproved apply must fail closed")