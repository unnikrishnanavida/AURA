"""Approval gate: no remediation activates without explicit authorization.

The gate is deliberately restrictive:
- an approver must be present and distinct from the requester,
- high/critical remediations require an approver with the ``security`` role,
- an approved decision records who approved, when, and why.

An unapproved plan NEVER reaches the canary or activation stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aura_security.models.remediation_plan import ChangeRequest, RemediationStatus


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approved: bool
    reason: str
    approver: str = ""
    approved_at: datetime | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "approver": self.approver,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class ApprovalGate:
    def __init__(self, *, required_roles: tuple[str, ...] = ("security",)) -> None:
        self._required_roles = required_roles
        self._records: list[ApprovalDecision] = []

    def approve(
        self,
        request: ChangeRequest,
        *,
        approver: str,
        roles: tuple[str, ...],
        note: str = "",
    ) -> ApprovalDecision:
        if not approver or approver == request.requested_by:
            decision = ApprovalDecision(
                approved=False,
                reason="approver must be present and distinct from requester",
                approver=approver,
            )
            self._records.append(decision)
            return decision

        severity = request.plan.assessment.severity.value
        if severity in {"high", "critical"} and not any(r in self._required_roles for r in roles):
            decision = ApprovalDecision(
                approved=False,
                reason=f"approver lacks required role for {severity} severity",
                approver=approver,
            )
            self._records.append(decision)
            return decision

        decision = ApprovalDecision(
            approved=True,
            reason=note or "approved",
            approver=approver,
            approved_at=datetime.now(UTC),
        )
        request_plan_status = RemediationStatus.APPROVED
        # freeze an immutable plan via replacement is complex; record approval
        # and rely on the engine to transition the plan.
        del request_plan_status
        self._records.append(decision)
        return decision

    def history(self) -> list[ApprovalDecision]:
        return list(self._records)


__all__ = ["ApprovalDecision", "ApprovalGate"]
