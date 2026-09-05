"""Adaptive defense domain shapes.

The threat model is intentionally conservative: a threat must satisfy
evidence thresholds before the pipeline proposes remediation, and every
remediation is staged behind validation, approval, canary, and rollback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from aura.foundation.ids import new_hex


class ThreatLevel(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefenseStage(StrEnum):
    DETECTED = "detected"
    CLASSIFIED = "classified"
    ASSESSED = "assessed"
    PROPOSED = "proposed"
    SANDBOXED = "sandboxed"
    APPROVED = "approved"
    CANARY = "canary"
    DEPLOYED = "deployed"
    MONITORED = "monitored"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


class RemediationStatus(StrEnum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class Threat:
    """One detected threat with its evidence and classification."""

    id: str = field(default_factory=lambda: f"th-{new_hex()}")
    name: str = ""
    level: ThreatLevel = ThreatLevel.INFO
    evidence: list[str] = field(default_factory=list)
    control_gap: str = ""
    root_cause: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "evidence_count": len(self.evidence),
            "control_gap": self.control_gap,
            "root_cause": self.root_cause,
        }


@dataclass(frozen=True, slots=True)
class DefenseDecision:
    """The pipeline's decision for one threat."""

    threat: Threat
    stage: DefenseStage
    remediation: str = ""
    reason: str = ""
    approved: bool = False
    canary: bool = False
    changes_tracked: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat": self.threat.name,
            "level": self.threat.level.value,
            "stage": self.stage.value,
            "remediation": self.remediation,
            "reason": self.reason,
            "approved": self.approved,
            "canary": self.canary,
        }


__all__ = ["DefenseDecision", "DefenseStage", "RemediationStatus", "Threat", "ThreatLevel"]