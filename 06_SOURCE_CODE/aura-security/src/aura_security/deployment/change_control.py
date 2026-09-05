"""Change control and rollback.

Tracks every plan transition so remediation is auditable and reversible.
Rollback can un-apply any activated remediation through an environment
callback; there is no implicit mutation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_security.models.remediation_plan import (
    RemediationPlan,
    RemediationStatus,
)


class ChangeControl:
    """Records each lifecycle transition of a remediation plan."""

    @dataclass
    class Entry:
        plan_id: str
        from_status: str
        to_status: str
        actor: str
        at: datetime = field(default_factory=lambda: datetime.now(UTC))

        def to_dict(self) -> dict[str, object]:
            return {
                "plan_id": self.plan_id,
                "from": self.from_status,
                "to": self.to_status,
                "actor": self.actor,
                "at": self.at.isoformat(),
            }

    def __init__(self) -> None:
        self._entries: list[ChangeControl.Entry] = []

    def record(
        self,
        plan: RemediationPlan,
        from_status: str,
        to_status: str,
        actor: str = "system",
    ) -> None:
        self._entries.append(
            ChangeControl.Entry(
                plan_id=plan.id,
                from_status=from_status,
                to_status=to_status,
                actor=actor,
            )
        )

    def entries(self) -> list[ChangeControl.Entry]:
        return list(self._entries)

    def plan_entries(self, plan_id: str) -> list[ChangeControl.Entry]:
        return [e for e in self._entries if e.plan_id == plan_id]


class RollbackManager:
    """Un-applies an activated remediation through an environment callback."""

    def __init__(self, change_control: ChangeControl | None = None) -> None:
        self._change_control = change_control or ChangeControl()
        self._rollbacks: list[str] = []

    def rollback(
        self,
        plan: RemediationPlan,
        *,
        undo: Callable[[RemediationPlan], None],
        actor: str = "operator",
    ) -> bool:
        if plan.status not in {RemediationStatus.ACTIVATED, RemediationStatus.MONITORED}:
            return False
        try:
            undo(plan)
        except (RuntimeError, ValueError, OSError):
            return False
        from_status = plan.status.value
        self._change_control.record(plan, from_status, RemediationStatus.ROLLED_BACK.value, actor=actor)
        self._rollbacks.append(plan.id)
        return True

    def rolled_back(self) -> list[str]:
        return list(self._rollbacks)


__all__ = ["ChangeControl", "RollbackManager"]
