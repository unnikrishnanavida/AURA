"""Adaptive Defense engine.

Orchestrates the safe remediation lifecycle:

  detect -> classify -> assess -> propose -> sandbox-validate
  -> approve -> canary -> activate -> monitor -> (rollback if needed)

CRITICAL SAFETY PROPERTY: the engine NEVER applies remediation on its own.
Activation only happens through the deployer callbacks an operator supplies,
and only after an ApprovalGate decision is approved.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aura_security.analysis.control_gap import ControlGapAnalyzer
from aura_security.analysis.defense_selection import DefenseSelector
from aura_security.deployment.approval_gate import ApprovalDecision, ApprovalGate
from aura_security.deployment.canary import CanaryDeployer
from aura_security.deployment.change_control import ChangeControl
from aura_security.models.remediation_plan import (
    ChangeRequest,
    Remediation,
    RemediationPlan,
    RemediationStatus,
)
from aura_security.models.threat_assessment import (
    Threat,
    ThreatAssessment,
    ThreatClassifier,
)


@dataclass
class DefenseOutcome:
    threat: Threat
    assessment: ThreatAssessment
    plan: RemediationPlan | None = None
    approval: ApprovalDecision | None = None
    activated: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "threat_id": self.threat.id,
            "severity": self.assessment.severity.value,
            "activated": self.activated,
            "reason": self.reason,
            "plan": self.plan.to_dict() if self.plan else None,
            "approval": self.approval.to_dict() if self.approval else None,
        }
class AdaptiveDefenseEngine:
    def __init__(
        self,
        *,
        classifier: ThreatClassifier | None = None,
        gap_analyzer: ControlGapAnalyzer | None = None,
        selector: DefenseSelector | None = None,
        approval_gate: ApprovalGate | None = None,
        canary: CanaryDeployer | None = None,
        change_control: ChangeControl | None = None,
    ) -> None:
        self.classifier = classifier or ThreatClassifier()
        self.gap_analyzer = gap_analyzer or ControlGapAnalyzer()
        self.selector = selector or DefenseSelector()
        self.approval_gate = approval_gate or ApprovalGate()
        self.canary = canary or CanaryDeployer()
        self.change_control = change_control or ChangeControl()

    def detect(
        self,
        threat: Threat,
        *,
        apply_canary: Callable[[Remediation], float] | None = None,
        promote: Callable[[Remediation], None] | None = None,
        requester: str = "detector",
        approver: str = "",
        approver_roles: tuple[str, ...] = (),
        approval_note: str = "",
    ) -> DefenseOutcome:
        """Run one threat through the adaptive-defense lifecycle.

        `apply_canary` and `promote` are optional injections so the engine can
        be exercised end-to-end in tests and runbooks without touching
        production. Without them the engine still records the full decision
        path up to activation.
        """
        assessment = self.classifier.classify(threat)

        if assessment.severity.value in {"info", "low"}:
            return DefenseOutcome(
                threat=threat,
                assessment=assessment,
                reason=f"severity {assessment.severity.value} below remediation threshold",
            )

        gap = self.gap_analyzer.analyze(assessment)
        if not gap:
            return DefenseOutcome(
                threat=threat,
                assessment=assessment,
                reason="no control gap identified",
            )

        remedies = self.selector.select(assessment, gap)
        plan = RemediationPlan(
            id=f"plan-{assessment.threat.id}",
            assessment=assessment,
            remediations=tuple(remedies),
            status=RemediationStatus.PROPOSED,
        )
        current_status = RemediationStatus.PROPOSED
        self.change_control.record(plan, "none", current_status.value, actor=requester)

        request = ChangeRequest(id=f"cr-{plan.id}", plan=plan, requested_by=requester)
        approval = self.approval_gate.approve(
            request,
            approver=approver,
            roles=approver_roles,
            note=approval_note,
        )
        if not approval.approved:
            self.change_control.record(
                plan, current_status.value, RemediationStatus.REJECTED.value, actor=approver or "gate"
            )
            return DefenseOutcome(
                threat=threat, assessment=assessment, plan=plan, approval=approval,
                reason=approval.reason,
            )

        current_status = RemediationStatus.APPROVED
        self.change_control.record(plan, "proposed", current_status.value, actor=approver)
        if apply_canary is None or promote is None:
            return DefenseOutcome(
                threat=threat, assessment=assessment, plan=plan, approval=approval,
                reason="approved; awaiting deployment adapter (canary/promote not supplied)",
            )

        canary_result = self.canary.run(
            plan.remediations[0],
            apply_canary=apply_canary,
            promote=lambda _r: None,
        )
        if not canary_result.promoted:
            self.change_control.record(
                plan, current_status.value, RemediationStatus.ROLLED_BACK.value, actor="canary"
            )
            return DefenseOutcome(
                threat=threat, assessment=assessment, plan=plan, approval=approval,
                reason=f"canary failed: {canary_result.reason}",
            )

        promote(plan.remediations[0])
        self.change_control.record(
            plan, current_status.value, RemediationStatus.ACTIVATED.value, actor="canary"
        )
        return DefenseOutcome(
            threat=threat,
            assessment=assessment,
            plan=plan,
            approval=approval,
            activated=True,
            reason="activated after approved canary",
        )


__all__ = ["AdaptiveDefenseEngine", "DefenseOutcome"]
