"""Remediation plan and change-request models.

A remediation is always a *proposal* the pipeline validates, sandboxes,
approves, canaries, and monitors before activating. There is no code path that
applies a remediation implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from aura_security.adaptive_defense_threats import AttackClass  # type: ignore[import-not-found]
from aura_security.adaptive_defense_threats import ThreatAssessment, ThreatSeverity


class RemediationKind(str, Enum):
    POLICY_CHANGE = "policy_change"
    SECRET_ROTATION = "secret_rotation"
    NETWORK_RULE = "network_rule"
    PATCH = "patch"
    CONFIG_HARDENING = "config_hardening"


class RemediationStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    SANDBOXED = "sandboxed"
    APPROVED = "approved"
    CANARY = "canary"
    ACTIVATED = "activated"
    MONITORED = "monitored"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Remediation:
    """One concrete remediation proposal tied to an assessment."""

    id: str
    kind: RemediationKind
    description: str
    scope: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "description": self.description,
            "scope": list(self.scope),
            "parameters": self.parameters,
        }


@dataclass(frozen=True, slots=True)
class RemediationPlan:
    """An ordered, versioned set of remediations for one threat."""

    id: str
    assessment: ThreatAssessment
    remediations: tuple[Remediation, ...]
    version: int = 1
    status: RemediationStatus = RemediationStatus.PROPOSED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assessment": self.assessment.to_dict(),
            "remediations": [r.to_dict() for r in self.remediations],
            "version": self.version,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class ChangeRequest:
    """A human/policy-approval request describing exactly what will change."""

    id: str
    plan: RemediationPlan
    requested_by: str
    approver: str = ""
    approved: bool = False
    approval_note: str = ""
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan.id,
            "requested_by": self.requested_by,
            "approver": self.approver,
            "approved": self.approved,
            "approval_note": self.approval_note,
        }


__all__ = [
    "ChangeRequest",
    "Remediation",
    "RemediationKind",
    "RemediationPlan",
    "RemediationStatus",
]
