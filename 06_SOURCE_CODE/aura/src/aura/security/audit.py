"""Audit logging.

Append-only audit trail for security-relevant decisions (permission denials,
safety reviews, approvals, learning updates). Never logs secret values -- the
record carries correlation ids and decision outcomes only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.serialization import to_jsonable


@dataclass
class AuditRecord:
    action: str
    actor: str
    resource: str
    decision: str
    reason: str
    timestamp: str
    correlation_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "resource": self.resource,
            "decision": self.decision,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "payload": to_jsonable(self.payload),
        }


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
        correlation_id: str | None = None,
        **payload: Any,
    ) -> AuditRecord:
        entry = AuditRecord(
            action=action,
            actor=actor,
            resource=resource,
            decision=decision,
            reason=reason,
            timestamp=self._clock.utcnow_iso(),
            correlation_id=correlation_id,
            payload=payload,
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


__all__ = ["AuditLog", "AuditRecord", "audit_log"]