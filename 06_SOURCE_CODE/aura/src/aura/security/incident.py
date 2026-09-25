"""Incident response.

Canonical incident lifecycle (DETECTED → TRIAGED → CONTAINED → INVESTIGATING →
REMEDIATING → RECOVERING → RESOLVED → CLOSED) with severity, evidence,
escalation, and an append-only audit trail. The manager is failure-safe:
record-keeping problems never mask the underlying security event.

This is a *control and coordination* framework, not a threat vendor: incidents
are raised from real signals (threat detectors, audit events, operator calls —
see :mod:`aura.security.threats`).
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from aura.foundation.clock import Clock, SystemClock

_VALID_STATES = (
    "DETECTED",
    "TRIAGED",
    "CONTAINED",
    "INVESTIGATING",
    "REMEDIATING",
    "RECOVERING",
    "RESOLVED",
    "CLOSED",
)

_ALLOWED_TRANSITIONS = {
    "DETECTED": {"TRIAGED", "CLOSED"},
    "TRIAGED": {"CONTAINED", "INVESTIGATING", "REMEDIATING", "CLOSED"},
    "CONTAINED": {"INVESTIGATING", "REMEDIATING", "RESOLVED"},
    "INVESTIGATING": {"CONTAINED", "REMEDIATING", "RESOLVED"},
    "REMEDIATING": {"INVESTIGATING", "RECOVERING", "RESOLVED"},
    "RECOVERING": {"RESOLVED"},
    "RESOLVED": {"CLOSED", "INVESTIGATING"},
    "CLOSED": set(),
}


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Incident:
    """One security incident with its immutable evidence trail."""

    incident_id: str
    title: str
    severity: IncidentSeverity
    source: str
    status: str = "DETECTED"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    owner: str | None = None

    def add_evidence(self, evidence: dict[str, Any]) -> None:
        self.evidence.append(dict(evidence))

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def snapshot(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity.value,
            "source": self.source,
            "status": self.status,
            "evidence": list(self.evidence),
            "notes": list(self.notes),
            "owner": self.owner,
        }


class IncidentManager:
    """Owns incidents; enforces the lifecycle; appends everything to audit."""

    def __init__(self, *, clock: Clock | None = None, audit: Any = None, max_open: int = 200) -> None:
        self._clock = clock or SystemClock()
        self._audit = audit
        self._incidents: dict[str, Incident] = {}
        self._max_open = max_open
        self._sequence = 0

    def _next_id(self) -> str:
        self._sequence += 1
        stamp = self._clock.utcnow_iso()[:10].replace("-", "")
        return f"inc-{stamp}-{self._sequence}"

    def _record_audit(self, action: str, incident_id: str, detail: str, severity: str) -> None:
        record = getattr(self._audit, "record", None)
        if callable(record):
            with contextlib.suppress(Exception):
                record(
                    action=f"incident.{action}",
                    actor="system",
                    resource=incident_id,
                    decision="tracked",
                    reason=detail,
                    payload={"severity": severity},
                )

    def open(
        self,
        *,
        title: str,
        severity: IncidentSeverity | str,
        source: str,
        evidence: dict[str, Any] | None = None,
    ) -> Incident:
        """Open a new DETECTED incident, or extend an existing open one with the
        same (title, severity, source)."""
        sev = severity if isinstance(severity, IncidentSeverity) else IncidentSeverity(severity)
        for existing in self._incidents.values():
            if (
                existing.title == title
                and existing.severity == sev
                and existing.source == source
                and existing.status != "CLOSED"
            ):
                if evidence:
                    existing.add_evidence(evidence)
                return existing
        incident = Incident(incident_id=self._next_id(), title=title, severity=sev, source=source)
        if evidence:
            incident.add_evidence(evidence)
        self._incidents[incident.incident_id] = incident
        if len(self._incidents) > self._max_open:
            closed = [i for i in self._incidents.values() if i.status == "CLOSED"]
            victim = closed[0] if closed else next(iter(self._incidents.values()))
            self._incidents.pop(victim.incident_id, None)
        self._record_audit("opened", incident.incident_id, title, sev.value)
        return incident

    def transition(self, incident_id: str, to: str, *, note: str | None = None, by: str = "system") -> bool:
        """Move an incident through the lifecycle; returns False on illegal moves."""
        incident = self._incidents.get(incident_id)
        if incident is None:
            return False
        to_state = to.upper()
        if to_state not in _VALID_STATES or to_state not in _ALLOWED_TRANSITIONS[incident.status]:
            return False
        incident.status = to_state
        if note:
            incident.add_note(f"[{by}] {note}")
        self._record_audit("transitioned", incident_id, f"{incident.status} -> {to_state}", incident.severity.value)
        return True

    def escalate(self, incident_id: str, *, severity: IncidentSeverity | str, by: str = "system") -> bool:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return False
        new_sev = severity if isinstance(severity, IncidentSeverity) else IncidentSeverity(severity)
        severity_rank = {sev: i for i, sev in enumerate(IncidentSeverity)}
        if severity_rank[new_sev] < severity_rank[incident.severity]:
            return False  # de-escalation is not allowed through escalate()
        incident.severity = new_sev
        incident.add_note(f"[{by}] escalated to {new_sev.value}")
        self._record_audit("escalated", incident_id, f"severity -> {new_sev.value}", new_sev.value)
        return True

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def open_incidents(self) -> list[Incident]:
        return [i for i in self._incidents.values() if i.status != "CLOSED"]

    def listing(self, *, status: str | None = None) -> list[dict[str, Any]]:
        items: list[Incident] = list(self._incidents.values())
        if status is not None:
            items = [i for i in items if i.status == status.upper()]
        return [i.snapshot() for i in items]


__all__ = ["Incident", "IncidentManager", "IncidentSeverity"]