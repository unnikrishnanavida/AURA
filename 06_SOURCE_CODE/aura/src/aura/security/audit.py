"""Audit logging.

Append-only audit trail for security-relevant decisions (permission denials,
safety reviews, approvals, learning updates). Never logs secret values -- the
record carries correlation ids and decision outcomes only.

Phase 27 (durable audit + production reliability): every record now carries a
stable ``event_id`` (:class:`aura.foundation.ids.EventId`) so records can be
replayed, resynced, and deduplicated across instances without weakening the
trail. :class:`AuditLog` stays the deterministic in-memory default; the durable
PostgreSQL implementation lives in ``aura.api.distributed``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import EventId
from aura.foundation.serialization import to_jsonable


@dataclass
class AuditRecord:
    action: str
    actor: str
    resource: str
    decision: str
    reason: str
    timestamp: str
    event_id: EventId | None = None
    correlation_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id) if self.event_id is not None else None,
            "action": self.action,
            "actor": self.actor,
            "resource": self.resource,
            "decision": self.decision,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "payload": to_jsonable(self.payload),
        }


def coerce_event_id(value: EventId | str | None) -> EventId:
    """Normalize an optional event id into a concrete :class:`EventId`.

    ``None`` yields a fresh id (callers that retry a logical event must pass the
    same id explicitly to stay idempotent).
    """
    if value is None:
        return EventId.new()
    if isinstance(value, EventId):
        return value
    return EventId.from_str(value)


class AuditLog:
    def __init__(self, clock: Clock | None = None, sink: Any | None = None) -> None:
        self._clock = clock or SystemClock()
        self._sink = sink  # optional callable(json_record) or file-like with write()
        self._records: list[AuditRecord] = []

    def record(
        self,
        *,
        action: str,
        actor: str,
        resource: str,
        decision: str,
        reason: str,
        event_id: EventId | str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
        **extra: Any,
    ) -> AuditRecord:
        """Record one audit decision.

        ``payload`` may be passed either as an explicit mapping (single ``payload=``
        keyword) or as flat extra keywords (``scopes=[...]``); both forms merge
        into the stored payload. The explicit parameter avoids the classic
        ``**payload`` name collision where ``payload={...}`` was bound as
        ``{"payload": {...}}``.
        """
        merged_payload: dict[str, Any] = dict(payload or {})
        merged_payload.update(extra)
        entry = AuditRecord(
            action=action,
            actor=actor,
            resource=resource,
            decision=decision,
            reason=reason,
            timestamp=self._clock.utcnow_iso(),
            event_id=coerce_event_id(event_id),
            correlation_id=correlation_id,
            payload=merged_payload,
        )
        self._records.append(entry)
        if self._sink is not None:
            raw = json.dumps(entry.to_dict(), sort_keys=True)
            write = getattr(self._sink, "write", None)
            if callable(write):
                write(raw + "\n")
            elif callable(self._sink):
                self._sink(raw)
        return entry

    def entries(self) -> list[AuditRecord]:
        return list(self._records)


_audit_log: AuditLog | None = None


def audit_log() -> AuditLog:
    """Return the process-wide audit log (injected where state is owned)."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


__all__ = ["AuditLog", "AuditRecord", "audit_log", "coerce_event_id"]