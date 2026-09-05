"""Approval manager: tracks explicit approvals for risky actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Approval:
    """A recorded approval for an action decision."""

    action_id: str
    approver: str
    granted: bool
    approved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    note: str = ""


class ApprovalManager:
    """In-memory approval store; missing approvals are treated as denied."""

    def __init__(self) -> None:
        self._approvals: dict[str, Approval] = {}

    def approve(self, action_id: str, approver: str, *, note: str = "") -> Approval:
        approval = Approval(action_id=action_id, approver=approver, granted=True, note=note)
        self._approvals[action_id] = approval
        return approval

    def reject(self, action_id: str, approver: str, *, note: str = "") -> Approval:
        approval = Approval(action_id=action_id, approver=approver, granted=False, note=note)
        self._approvals[action_id] = approval
        return approval

    def get(self, action_id: str) -> Approval | None:
        return self._approvals.get(action_id)

    def is_approved(self, action_id: str) -> bool:
        approval = self._approvals.get(action_id)
        return approval is not None and approval.granted


__all__ = ["Approval", "ApprovalManager"]