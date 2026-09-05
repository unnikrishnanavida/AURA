"""Adaptive defense models: threat assessment, remediation, approval, canary.

Re-exports the authoritative implementations in :mod:`aura_security.models`.
"""

from __future__ import annotations

from aura_security.models.remediation_plan import (
    ChangeRequest,
    Remediation,
    RemediationKind,
    RemediationPlan,
    RemediationStatus,
)
from aura_security.models.threat_assessment import (
    AttackClass,
    Threat,
    ThreatAssessment,
    ThreatClassifier,
    ThreatSeverity,
)

__all__ = [
    "AttackClass",
    "ChangeRequest",
    "Remediation",
    "RemediationKind",
    "RemediationPlan",
    "RemediationStatus",
    "Threat",
    "ThreatAssessment",
    "ThreatClassifier",
    "ThreatSeverity",
]
