"""Workstream 3 — learning/reflection connected to REAL execution evidence.

Uses a real denied workspace action as the evidence, feeds it into the
reflection + learning pipeline, and proves: evidence is referenced, nothing is
invented, proposals are not silently applied, and authorized changes are
versioned + reversible.
"""

from __future__ import annotations

from pathlib import Path

from aura.brain.engine import BrainEngine
from aura.core.pipeline import default_guardrails
from aura.execution.actions import WorkspaceManager
from aura.execution.engine import ExecutionEngine, ExecutionRequest, ExecutionResult
from aura.execution.models import ActionInputs, WorldState
from aura.execution.registry import ActionRegistry
from aura.learning.models import LearningSignal, SignalStatus
from aura.reflection.models import SignalKind as ReflectionSignalKind
from aura.security.audit import AuditLog


def _real_denied_evidence(tmp_path: Path) -> ExecutionResult:
    """Produce a genuine execution failure through the secure action family."""
    manager = WorkspaceManager(workspaces_root=tmp_path / "wsroot", audit=AuditLog())
    registry = ActionRegistry()
    manager.install(registry)
    engine = ExecutionEngine(registry=registry, guardrails=default_guardrails(registry))
    return engine.execute(
        ExecutionRequest(
            action="process.run",
            inputs=ActionInputs(values={"command": "powershell", "args": ["/C", "nonsense"]}),
            world_state=WorldState(values={}),
            approval=True,  # gate passes; the allowlist must still deny
        )
    )


def test_reflection_references_real_execution_evidence(tmp_path: Path) -> None:
    brain = BrainEngine.create(seed=3)
    evidence = _real_denied_evidence(tmp_path)
    assert not evidence.ok
    deviation = evidence.action_result.error  # real message from the rejected action

    result = brain.reflect_and_learn(
        goal="run an approved verifier command",
        success=False,
        observed={"process_run_ok": False},
        expected={"process_run_ok": True},
        deviations=[deviation],
        events_summary=[f"process.run denied: {deviation}"],
    )
    kinds = {s.kind for s in result.reflections}
    assert ReflectionSignalKind.FAILURE_REVIEW in kinds
    assert ReflectionSignalKind.IMPROVEMENT_SUGGESTION in kinds
    # The reflection must reference the actual evidence, not a generic excuse.
    assert any("powershell" in s.content for s in result.reflections)
    # A learning.signal flight event is the traceable audit trail.
    assert any(e.event_type == "learning.signal" for e in brain.recorder.events())


def test_reflection_does_not_invent_missing_evidence(tmp_path: Path) -> None:
    brain = BrainEngine.create(seed=3)
    result = brain.reflect_and_learn(
        goal="succeeded cleanly",
        success=True,
        deviations=[],
        events_summary=["step completed"],
    )
    for signal in result.reflections:
        assert "powershell" not in signal.content
        assert "not allowlisted" not in signal.content


def test_proposed_changes_not_silently_applied_and_authorized_changes_roll_back(
    tmp_path: Path,
) -> None:
    brain = BrainEngine.create(seed=3)
    evidence = _real_denied_evidence(tmp_path)
    deviation = evidence.action_result.error

    # (1) A safety-relevant proposal derived from REAL evidence must be rejected
    #     until explicitly authorized — never silently applied.
    proposal = LearningSignal.create(
        kind="safety_policy_change",
        content=(
            "propose allowing 'powershell' after a failed verifier run "
            f"(evidence: {deviation})"
        ),
        evidence=[{"score": 0.8}],
    )
    proposal.safety_relevant = True
    rejected = brain.learning.submit(proposal)
    assert rejected.outcome.approved is False
    assert "authorization" in rejected.outcome.reason
    assert proposal.status is SignalStatus.REJECTED
    assert brain.learning.registry.active() == []

    # (2) A validated, authorized change is versioned, active, and invertible.
    change_signal = LearningSignal.create(
        kind="strategy_improvement",
        content="verify command allowlist before approval flows",
        evidence=[{"score": 0.8}],
    )
    applied = brain.learning.approve_and_apply(change_signal, authorized=True)
    assert applied.applied and applied.change is not None
    active = brain.learning.registry.active()
    assert any(c.ref == applied.change.ref for c in active)

    rolled = brain.learning.rollback(applied.change.ref)
    assert rolled.rolled_back_at is not None
    assert change_signal.status is SignalStatus.ROLLED_BACK
    assert brain.learning.registry.active() == []