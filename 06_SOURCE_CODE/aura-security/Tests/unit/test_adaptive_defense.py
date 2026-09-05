"""Unit tests for AURA Adaptive Defense.

Verify the safe remediation lifecycle:

  detect -> classify -> assess -> propose -> approve -> canary -> activate

Critical safety properties under test:
  1. low-severity threats never produce remediation plans,
  2. a missing approver blocks activation,
  3. an unhealthy canary never reaches activation,
  4. activation only occurs after explicit approval through injected callbacks,
  5. every transition is recorded by change control.
"""

from __future__ import annotations

from aura_security import AdaptiveDefenseEngine, Threat
from aura_security.models.remediation_plan import Remediation


def _engine() -> AdaptiveDefenseEngine:
    return AdaptiveDefenseEngine()


def _sql_threat() -> Threat:
    return Threat(
        id="t-sql",
        kind="sql injection detected",
        indicators={"pattern": "SELECT * FROM users"},
    )


def test_sql_threat_classified_injection() -> None:
    eng = _engine()
    out = eng.detect(_sql_threat(), approver="soc.admin", approver_roles=("security",))
    assert out.assessment.attack_class.value == "injection"
    assert out.assessment.severity.value == "medium"


def test_low_severity_never_proposes_remediation() -> None:
    eng = _engine()
    low = eng.detect(Threat(id="t-low", kind="info log", indicators={"sev": "info"}))
    assert low.plan is None
    assert "below remediation threshold" in low.reason


def test_missing_approver_blocks_activation() -> None:
    eng = _engine()
    out = eng.detect(_sql_threat())
    assert not out.activated
    assert out.approval is not None and not out.approval.approved
    assert "approver" in out.reason


def test_approver_without_role_blocks_high_severity() -> None:
    eng = _engine()
    threat = Threat(id="t-secret", kind="api key leaked", indicators={"secret": "AKIA..."})
    out = eng.detect(threat, requester="detector", approver="jane", approver_roles=("viewer",))
    assert not out.activated
    assert "role" in out.reason


def test_approved_but_no_canary_adapter_pending() -> None:
    eng = _engine()
    out = eng.detect(
        _sql_threat(), requester="detector", approver="soc.admin", approver_roles=("security",)
    )
    assert out.approval is not None and out.approval.approved
    assert not out.activated
    assert "deployment adapter" in out.reason


def test_healthy_canary_enables_activation() -> None:
    eng = _engine()
    promoted = {"n": 0}

    def healthy(_r: Remediation) -> float:
        return 0.95

    def promote(_r: Remediation) -> None:
        promoted["n"] += 1

    out = eng.detect(
        _sql_threat(),
        requester="detector",
        approver="soc.admin",
        approver_roles=("security",),
        apply_canary=healthy,
        promote=promote,
    )
    assert out.activated
    assert promoted["n"] == 1


def test_unhealthy_canary_rolls_back() -> None:
    eng = _engine()
    out = eng.detect(
        _sql_threat(),
        requester="detector",
        approver="soc.admin",
        approver_roles=("security",),
        apply_canary=lambda _r: 0.3,
        promote=lambda _r: None,
    )
    assert not out.activated
    assert "canary failed" in out.reason


def test_change_control_records_lifecycle() -> None:
    eng = _engine()
    out = eng.detect(
        _sql_threat(),
        requester="detector",
        approver="soc.admin",
        approver_roles=("security",),
        apply_canary=lambda _r: 0.9,
        promote=lambda _r: None,
    )
    entries = eng.change_control.entries()
    assert len(entries) >= 3  # proposed -> approved -> activated
    statuses = [e.to_status for e in entries]
    assert "proposed" in statuses
    assert "approved" in statuses
    assert "activated" in statuses


def test_strict_sandbox_threshold_blocks_activation() -> None:
    """A canary below the sandbox's strict threshold never activates."""
    eng = _engine()
    eng.canary._min_health_score = 1.0
    out = eng.detect(
        _sql_threat(),
        requester="detector",
        approver="soc.admin",
        approver_roles=("security",),
        apply_canary=lambda _r: 0.99,  # below the 1.0 threshold
        promote=lambda _r: None,
    )
    assert not out.activated
    assert "canary failed" in out.reason