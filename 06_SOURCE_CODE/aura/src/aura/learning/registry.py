"""Versioned learned-behavior registry with lineage and rollback."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura.foundation.errors import NotFoundError
from aura.learning.models import LearningSignal, SignalStatus


def _encode_dt(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _decode_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


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
    def __init__(self, state_path: str | None = None) -> None:
        self._changes: dict[str, AppliedChange] = {}
        self._lineage: dict[str, str] = {}
        self._store = None
        if state_path:
            from aura.foundation.persistent import SQLiteJsonStore

            self._store = SQLiteJsonStore(state_path, table="learning")
            self._hydrate()

    # -- durability ----------------------------------------------------------

    def _persist(self) -> None:
        if self._store is None:
            return
        snapshot = {
            "changes": [self._encode_change(c) for c in self._changes.values()],
            "lineage": dict(self._lineage),
        }
        with contextlib.suppress(Exception):  # persistence must not break learning safety
            self._store.put("v1", snapshot)

    def _hydrate(self) -> None:
        if self._store is None:
            return
        try:
            snap = self._store.get("v1") or {}
        except Exception:  # noqa: BLE001 - corrupt state must not block startup
            snap = {}
        for change_dict in snap.get("changes", []):
            try:
                change = self._decode_change(change_dict)
            except Exception:  # noqa: BLE001
                continue
            self._changes[change.ref] = change
        self._lineage = {str(k): str(v).replace("\\", "") for k, v in (snap.get("lineage") or {}).items()}

    @staticmethod
    def _encode_change(change: AppliedChange) -> dict[str, Any]:
        sig = change.signal
        return {
            "ref": change.ref,
            "signal": {
                "id": sig.id,
                "kind": sig.kind,
                "content": sig.content,
                "status": sig.status.value,
                "safety_relevant": sig.safety_relevant,
                "authorized": sig.authorized,
                "created_at": _encode_dt(sig.created_at),
                "applied_ref": sig.applied_ref,
            },
            "applied_at": _encode_dt(change.applied_at),
            "lineage": change.lineage,
            "rolled_back_at": _encode_dt(change.rolled_back_at),
            "metadata": change.metadata,
        }

    @staticmethod
    def _decode_change(data: dict[str, Any]) -> AppliedChange:
        sig_data = data.get("signal") or {}
        signal = LearningSignal(
            id=sig_data["id"],
            kind=sig_data.get("kind", "lesson"),
            content=sig_data.get("content", ""),
            status=SignalStatus(sig_data.get("status", "candidate")),
            safety_relevant=bool(sig_data.get("safety_relevant", False)),
            authorized=bool(sig_data.get("authorized", False)),
            created_at=_decode_dt(sig_data.get("created_at")) or datetime.now(UTC),
            applied_ref=sig_data.get("applied_ref"),
        )
        return AppliedChange(
            ref=data["ref"],
            signal=signal,
            applied_at=_decode_dt(data.get("applied_at")) or datetime.now(UTC),
            lineage=data.get("lineage"),
            rolled_back_at=_decode_dt(data.get("rolled_back_at")),
            metadata=data.get("metadata") or {},
        )

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
        self._persist()
        return change

    def rollback(self, ref: str) -> AppliedChange:
        if ref not in self._changes:
            raise NotFoundError(f"no applied change with ref {ref!r}")
        change = self._changes[ref]
        if change.rolled_back_at is not None:
            return change
        change.rolled_back_at = datetime.now(UTC)
        change.signal.status = SignalStatus.ROLLED_BACK
        self._persist()
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