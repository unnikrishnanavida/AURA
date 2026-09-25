"""Compliance readiness framework.

A generic control/evidence registry: control ID, requirement, implementation
reference, evidence, status, owner, and an append-only audit history.

Honest scope:
- This provides *compliance readiness* (mapping, evidence collection,
  status tracking) — it does NOT claim legal/regulatory certification.
- Status values: NOT_STARTED / IN_PROGRESS / IMPLEMENTED / VERIFIED / N_A.
- Evidence is added by the control owner or automation and is append-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from aura.foundation.clock import Clock, SystemClock


class ControlStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    N_A = "n/a"


@dataclass
class ControlRecord:
    control_id: str
    requirement: str
    implementation: str
    owner: str
    status: ControlStatus = ControlStatus.NOT_STARTED
    evidence: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def set_status(self, status: ControlStatus | str, *, changed_by: str, note: str = "") -> None:
        new = status if isinstance(status, ControlStatus) else ControlStatus(status)
        self.history.append(
            {"from": self.status.value, "to": new.value, "by": changed_by, "note": note}
        )
        self.status = new

    def add_evidence(self, evidence: dict[str, Any], *, collected_by: str) -> None:
        record = dict(evidence)
        record["collected_by"] = collected_by
        self.evidence.append(record)

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "requirement": self.requirement,
            "implementation": self.implementation,
            "owner": self.owner,
            "status": self.status.value,
            "evidence_count": len(self.evidence),
        }


class ComplianceRegistry:
    """Registry of controls with evidence and audit history."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._controls: dict[str, ControlRecord] = {}

    def add(self, record: ControlRecord) -> None:
        self._controls[record.control_id] = record

    def ensure(self, **fields: Any) -> ControlRecord:
        control_id = str(fields["control_id"])
        if control_id in self._controls:
            return self._controls[control_id]
        record = ControlRecord(**fields)
        self._controls[control_id] = record
        return record

    def get(self, control_id: str) -> ControlRecord | None:
        return self._controls.get(control_id)

    def by_status(self, status: ControlStatus | str) -> list[ControlRecord]:
        target = status.value if isinstance(status, ControlStatus) else status
        return [c for c in self._controls.values() if c.status.value == target]

    def listing(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in sorted(self._controls.values(), key=lambda c: c.control_id)]

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self._controls.values():
            counts[record.status.value] = counts.get(record.status.value, 0) + 1
        return counts


__all__ = ["ComplianceRegistry", "ControlRecord", "ControlStatus"]