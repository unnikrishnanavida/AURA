"""Deployment audit events for aura-cloud (append-only ledger)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ChangeEvent:
    """One auditable deployment event."""

    plan_id: str
    event_type: str  # planned | deployed | rolled_back | rejected
    provider: str
    detail: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "event_type": self.event_type,
            "provider": self.provider,
            "detail": self.detail,
            "occurred_at": self.occurred_at.isoformat(),
        }


class DeploymentAudit:
    """Append-only deployment audit trail."""

    def __init__(self) -> None:
        self._events: list[ChangeEvent] = []

    def record(self, *, plan_id: str, event_type: str, provider: str, detail: str) -> ChangeEvent:
        event = ChangeEvent(plan_id=plan_id, event_type=event_type, provider=provider, detail=detail)
        self._events.append(event)
        return event

    def for_plan(self, plan_id: str) -> list[ChangeEvent]:
        return [e for e in self._events if e.plan_id == plan_id]

    def __len__(self) -> int:
        return len(self._events)


__all__ = ["ChangeEvent", "DeploymentAudit"]