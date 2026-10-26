"""Audit integration for aura-api.

Every security-relevant event (authentication, authorization, rate-limit
denial, validation failure) is recorded with the correlation ID, timestamp,
and a redacted detail string. The audit log is append-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from aura_api.core.errors import redact


@dataclass
class AuditEvent:
    """One immutable audit record."""

    correlation_id: str
    event_type: str
    detail: str
    subject: str | None = None
    outcome: str = "denied"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "event_type": self.event_type,
            "detail": redact(self.detail),
            "subject": self.subject,
            "outcome": self.outcome,
            "occurred_at": self.occurred_at.isoformat(),
        }


class AuditLogger:
    """Append-only audit trail."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        *,
        correlation_id: str,
        event_type: str,
        detail: str,
        subject: str | None = None,
        outcome: str = "denied",
    ) -> AuditEvent:
        event = AuditEvent(
            correlation_id=correlation_id,
            event_type=event_type,
            detail=detail,
            subject=subject,
            outcome=outcome,
        )
        self._events.append(event)
        return event

    def events(self) -> list[AuditEvent]:
        return list(self._events)

    def for_correlation(self, correlation_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.correlation_id == correlation_id]


__all__ = ["AuditEvent", "AuditLogger"]