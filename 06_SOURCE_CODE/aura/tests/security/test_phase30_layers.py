"""Phase 30 tests: incident lifecycle, threat detection, privacy, encryption, compliance."""

from __future__ import annotations


def base64_urlsafe(nbytes: int) -> str:
    import base64
    import os

    return base64.urlsafe_b64encode(os.urandom(nbytes)).decode("ascii")


def test_incident_lifecycle_happy_path() -> None:
    from aura.security.incident import IncidentManager, IncidentSeverity

    manager = IncidentManager()
    incident = manager.open(title="brute force", severity=IncidentSeverity.HIGH, source="detector")
    assert incident.status == "DETECTED"
    for state in ("triaged", "contained", "investigating", "remediating", "recovering", "resolved", "closed"):
        assert manager.transition(incident.incident_id, state)
    assert manager.get(incident.incident_id) is not None
    assert manager.open_incidents() == []
    assert len(manager.listing(status="DETECTED")) == 0


def test_incident_rejects_illegal_transitions() -> None:
    from aura.security.incident import IncidentManager, IncidentSeverity

    manager = IncidentManager()
    incident = manager.open(title="x", severity=IncidentSeverity.LOW, source="test")
    assert manager.transition(incident.incident_id, "resolved") is False
    assert incident.status == "DETECTED"
    assert manager.transition("does-not-exist", "closed") is False


def test_incident_escalation_monotonic() -> None:
    from aura.security.incident import IncidentManager, IncidentSeverity

    manager = IncidentManager()
    incident = manager.open(title="x", severity=IncidentSeverity.LOW, source="test")
    assert manager.escalate(incident.incident_id, severity=IncidentSeverity.CRITICAL) is True
    assert manager.escalate(incident.incident_id, severity=IncidentSeverity.LOW) is False


def test_incident_dedup_and_evidence() -> None:
    from aura.security.incident import IncidentManager, IncidentSeverity

    manager = IncidentManager()
    first = manager.open(title="t", severity=IncidentSeverity.MEDIUM, source="s", evidence={"n": 1})
    second = manager.open(title="t", severity=IncidentSeverity.MEDIUM, source="s", evidence={"n": 2})
    assert first.incident_id == second.incident_id
    assert len(first.evidence) == 2


def test_incident_audits_to_audit_log() -> None:
    from aura.security.audit import AuditLog
    from aura.security.incident import IncidentManager

    audit = AuditLog()
    manager = IncidentManager(audit=audit)
    manager.open(title="t", severity="high", source="s")
    assert any(r.action == "incident.opened" for r in audit.entries())


def test_threat_monitor_opens_incidents() -> None:
    from aura.security.incident import IncidentManager
    from aura.security.threats import (
        BruteForceDetector,
        PrivilegeViolationDetector,
        RateAbuseDetector,
        ThreatMonitor,
    )

    manager = IncidentManager()
    monitor = ThreatMonitor(
        manager,
        [BruteForceDetector(threshold=3), RateAbuseDetector(threshold=5), PrivilegeViolationDetector(threshold=2)],
    )
    opened = monitor.assess(auth_failures={"10.0.0.1": 4}, rate_denials={"10.0.0.2": 6}, authz_denials={"alice": 2})
    assert {i.title for i in opened} == {
        "brute-force authentication attempt",
        "rate-limit abuse",
        "authorization violations",
    }
    assert len(manager.open_incidents()) == 3


def test_threat_detector_window_and_reset() -> None:
    from aura.security.threats import BruteForceDetector

    detector = BruteForceDetector(threshold=2, window_seconds=300)
    assert detector.analyze(ip="a") is False
    assert detector.analyze(ip="a") is True
    detector.reset()
    assert detector.counts() == {}


def test_privacy_redaction_and_retention() -> None:
    from aura.memory.models import Sensitivity
    from aura.security.privacy import PrivacyGate, RedactionPolicy, RetentionDecision

    gate = PrivacyGate(redaction_policy=RedactionPolicy(allow=("decision",)))
    result = gate.redact({"decision": "allow", "prompt": "secret", "extra": 1}, sensitivity=Sensitivity.RESTRICTED)
    assert result.redacted == {"decision": "allow"}
    assert "prompt" in result.dropped_fields
    pub = gate.redact({"anything": 1}, sensitivity=Sensitivity.PUBLIC)
    assert pub.redacted == {"anything": 1}
    assert gate.retention(expires_at=None, now=0) is RetentionDecision.KEEP
    assert gate.retention(expires_at=1, now=2) is RetentionDecision.EXPIRE


def test_encryption_roundtrip_and_rotation() -> None:
    from aura.security.encryption import FernetCipher

    cipher = FernetCipher(key=base64_urlsafe(32))
    sealed = cipher.encrypt("sensitive-value")
    assert cipher.decrypt(sealed) == "sensitive-value"
    cipher.rotate_to(base64_urlsafe(32))
    assert cipher.decrypt(sealed) == "sensitive-value"  # old key still valid
    fresh = cipher.encrypt("new")
    assert cipher.decrypt(fresh) == "new"


def test_encryption_requires_key() -> None:
    from aura.foundation.errors import ConfigurationError
    from aura.security.encryption import FernetCipher

    try:
        FernetCipher()  # type: ignore[call-arg]
        raise AssertionError("expected ConfigurationError")
    except ConfigurationError:
        pass


def test_compliance_registry() -> None:
    from aura.security.compliance import ComplianceRegistry, ControlStatus

    registry = ComplianceRegistry()
    control = registry.ensure(
        control_id="SOX.1",
        requirement="audit trail exists",
        implementation="aura.security.audit",
        owner="sec-team",
    )
    control.add_evidence({"test": "audit_roundtrip"}, collected_by="pipeline")
    control.set_status(ControlStatus.VERIFIED, changed_by="auditor", note="evidence reviewed")
    assert registry.get("SOX.1").status is ControlStatus.VERIFIED
    assert registry.summary()["verified"] == 1
    assert len(control.history) == 1