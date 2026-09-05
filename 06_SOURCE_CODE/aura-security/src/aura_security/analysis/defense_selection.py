"""Defense selection.

Maps an assessed threat + control gap to one concrete remediation proposal.
Selection is deterministic and conservative: it proposes the smallest change
that closes the identified gap.
"""

from __future__ import annotations

from typing import ClassVar

from aura_security.analysis.control_gap import ControlGap
from aura_security.models.remediation_plan import Remediation, RemediationKind
from aura_security.models.threat_assessment import AttackClass, ThreatAssessment


class DefenseSelector:
    _KIND_BY_CLASS: ClassVar[dict[AttackClass, RemediationKind]] = {
        AttackClass.INJECTION: RemediationKind.POLICY_CHANGE,
        AttackClass.PATH_TRAVERSAL: RemediationKind.CONFIG_HARDENING,
        AttackClass.AUTH_BYPASS: RemediationKind.POLICY_CHANGE,
        AttackClass.PERMISSION_ESCALATION: RemediationKind.POLICY_CHANGE,
        AttackClass.SECRET_EXPOSURE: RemediationKind.SECRET_ROTATION,
        AttackClass.RESOURCE_EXHAUSTION: RemediationKind.CONFIG_HARDENING,
        AttackClass.SUPPLY_CHAIN: RemediationKind.PATCH,
        AttackClass.UNKNOWN: RemediationKind.CONFIG_HARDENING,
    }

    def select(self, assessment: ThreatAssessment, gap: ControlGap) -> list[Remediation]:
        kind = self._KIND_BY_CLASS[assessment.attack_class]
        return [
            Remediation(
                id=f"rem-{assessment.threat.id}",
                kind=kind,
                description=f"close control gap {gap.control}: {gap.description}",
                scope=(gap.control,),
                parameters={"severity": assessment.severity.value},
            )
        ]


__all__ = ["DefenseSelector"]
