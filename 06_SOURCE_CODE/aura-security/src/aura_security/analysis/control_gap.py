"""Control gap analysis.

Identifies which security control failed to halt an assessed threat. A gap is
a human-readable statement of what the control should have prevented, so the
defense selector can propose a matching remediation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from aura_security.models.threat_assessment import AttackClass, ThreatAssessment


@dataclass(frozen=True, slots=True)
class ControlGap:
    control: str
    description: str

    def __bool__(self) -> bool:
        return bool(self.control)

    def __str__(self) -> str:
        return f"{self.control}: {self.description}"


class ControlGapAnalyzer:
    """Maps an attack class to the security control that should have stopped it."""

    _GAPS: ClassVar[dict[AttackClass, ControlGap]] = {
        AttackClass.INJECTION: ControlGap(
            "input-validation",
            "input validation failed; untrusted input reached an interpreter",
        ),
        AttackClass.PATH_TRAVERSAL: ControlGap(
            "path-sandbox",
            "path sandbox failed; traversal outside allowed directory",
        ),
        AttackClass.AUTH_BYPASS: ControlGap(
            "authentication",
            "authentication boundary was bypassed",
        ),
        AttackClass.PERMISSION_ESCALATION: ControlGap(
            "authorization",
            "authorization check allowed a privilege the subject does not hold",
        ),
        AttackClass.SECRET_EXPOSURE: ControlGap(
            "secret-management",
            "secret management failed; a credential was disclosed",
        ),
        AttackClass.RESOURCE_EXHAUSTION: ControlGap(
            "resource-limits",
            "resource limits failed; consumption was unbounded",
        ),
        AttackClass.SUPPLY_CHAIN: ControlGap(
            "dependency-scanning",
            "dependency scanning failed to gate a vulnerable package",
        ),
        AttackClass.UNKNOWN: ControlGap(
            "",
            "unclassified threat; no specific control gap identified",
        ),
    }

    def analyze(self, assessment: ThreatAssessment) -> ControlGap:
        return self._GAPS[assessment.attack_class]


__all__ = ["ControlGap", "ControlGapAnalyzer"]
