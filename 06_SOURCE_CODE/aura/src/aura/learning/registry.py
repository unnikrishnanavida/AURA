"""Versioned learned-behavior registry with lineage and rollback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura.foundation.errors import NotFoundError
from aura.learning.models import LearningSignal, SignalStatus


@dataclass
class AppliedChange:
    ref: str
    signal: LearningSignal
    applied_at: datetime
    lineage: str | None = None
    rolled_back_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.rolled_back_at is None


class LearningRegistry:
    def __init__(self) -> None:
        self._changes: dict[str, AppliedChange] = {}
        self._lineage: dict[str, str] = {}

    def apply(self, signal: LearningSignal, *, parent: str | None = None) -> AppliedChange:
        ref = f"chg-{signal.id.split('-', 1)[-1]}"
        change = AppliedChange(
            ref=ref,
            signal=signal,
            applied_at=datetime.now(UTC),
            lineage=parent or self._lineage.get(signal.id),
        )
        self._changes[ref] = change
        if parent:
            self._lineage[signal.id] = parent
        signal.status = SignalStatus.APPLIED
        signal.applied_ref = ref
        return change

    def rollback(self, ref: str) -> AppliedChange:
        if ref not in self._changes:
            raise NotFoundError(f"no applied change with ref {ref!r}")
        change = self._changes[ref]
        if change.rolled_back_at is not None:
            return change
        change.rolled_back_at = datetime.now(UTC)
        change.signal.status = SignalStatus.ROLLED_BACK
        return change

    def active(self) -> list[AppliedChange]:
        return [c for c in self._changes.values() if c.active]

    def history(self, signal_id: str | None = None) -> list[AppliedChange]:
        if signal_id is None:
            return list(self._changes.values())
        return [c for c in self._changes.values() if c.signal.id == signal_id]

    def lineage_of(self, signal_id: str) -> list[str]:
        chain: list[str] = []
        cursor = self._lineage.get(signal_id)
        visited: set[str] = set()
        while cursor and cursor not in visited:
            visited.add(cursor)
            chain.append(cursor)
            cursor = self._lineage.get(cursor)
        return chain


__all__ = ["AppliedChange", "LearningRegistry"]