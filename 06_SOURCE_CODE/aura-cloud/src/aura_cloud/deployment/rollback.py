"""Rollback contract for aura-cloud deployments with a real rollback ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class RollbackRecord:
    """A recorded rollback action."""

    plan_id: str
    provider: str
    reason: str
    rolled_back_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "provider": self.provider,
            "reason": self.reason,
            "rolled_back_at": self.rolled_back_at.isoformat(),
        }


class RollbackLedger:
    """Append-only ledger of every rollback, with per-plan lookup."""

    def __init__(self) -> None:
        self._records: list[RollbackRecord] = []

    def record(self, plan_id: str, provider: str, reason: str) -> RollbackRecord:
        record = RollbackRecord(plan_id=plan_id, provider=provider, reason=reason)
        self._records.append(record)
        return record

    def for_plan(self, plan_id: str) -> list[RollbackRecord]:
        return [r for r in self._records if r.plan_id == plan_id]

    def __len__(self) -> int:
        return len(self._records)


__all__ = ["RollbackLedger", "RollbackRecord"]