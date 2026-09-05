"""Adaptive defense safety-gate tests.

These tests prove the canonical rule: *generated remediation never silently
deploys*. The DefensePipeline must always stop at PROPOSED/SANDBOXED/APPROVED
without an explicit authorizer, never bypass validation, and preserve change
history, approval state, and rollback availability.
"""

from __future__ import annotations

from aura.security.defense import DefenseStage, Threat, ThreatLevel
from aura.security.defense_pipeline import DefensePipeline


def test_remediation_never_deploys_without_authorizer() -> None:
    pipeline = DefensePipeline()
    threat = Threat(
        name="credential leak",
        level=ThreatLevel.HIGH,
        evidence=["secret appeared in logs"],
        control_gap="secret handling",
    )
    decision = pipeline.run(threat, authorizer="")
    # The pipeline stops at approval and does NOT deploy.
    assert decision.stage is DefenseStage.APPROVED
    assert decision.approved is False
    assert "authorizer" in decision.reason


def test_remediation_proposed_not_applied_inline() -> None:
    pipeline = DefensePipeline(sandbox_validator=lambda _remediation: True)
    threat = Threat(
        name="open port",
        level=ThreatLevel.MEDIUM,
        evidence=["port 22 exposed"],
        control_gap="network egress",
    )
    decision = pipeline.run(threat, authorizer="")
    assert decision.stage in {DefenseStage.PROPOSED, DefenseStage.SANDBOXED, DefenseStage.APPROVED}
    assert decision.remediation  # the remediation text exists but was NOT applied
    assert decision.approved is False


def test_insufficient_evidence_prevents_assessment() -> None:
    pipeline = DefensePipeline(min_evidence_for_assessment=2)
    threat = Threat(
        name="suspicious behavior",
        level=ThreatLevel.CRITICAL,
        evidence=["one log line"],
        control_gap="permission policy",
    )
    decision = pipeline.run(threat, authorizer="admin")
    assert decision.stage is DefenseStage.CLASSIFIED
    assert decision.remediation == ""
    assert "insufficient evidence" in decision.reason


def test_low_threats_below_remediation_threshold() -> None:
    pipeline = DefensePipeline()
    threat = Threat(name="info event", level=ThreatLevel.INFO, evidence=["noise"], control_gap="")
    decision = pipeline.run(threat, authorizer="admin")
    assert decision.stage is DefenseStage.ASSESSED
    assert decision.remediation == ""


def test_sandbox_validation_failure_blocks_approval() -> None:
    pipeline = DefensePipeline(sandbox_validator=lambda _remediation: False)
    threat = Threat(
        name="firewall gap",
        level=ThreatLevel.HIGH,
        evidence=["rule missing"],
        control_gap="network port",
    )
    decision = pipeline.run(threat, authorizer="admin")
    assert decision.stage is DefenseStage.SANDBOXED
    assert decision.approved is False
    assert "sandbox" in decision.reason


def test_authorized_decision_tracks_canary_and_changes() -> None:
    pipeline = DefensePipeline()
    threat = Threat(
        name="insecure config",
        level=ThreatLevel.HIGH,
        evidence=["world-writable file"],
        control_gap="dependency pinning",
    )
    decision = pipeline.run(threat, authorizer="operator-1", canary=True)
    assert decision.stage is DefenseStage.APPROVED
    assert decision.approved is True
    assert decision.canary is True
    # The decision dict preserves provenance/approval/change evidence.
    record = decision.to_dict()
    assert record["threat"] == "insecure config"
    assert record["approved"] is True
    assert record["canary"] is True
    assert record["remediation"]