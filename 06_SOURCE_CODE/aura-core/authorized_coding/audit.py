"""Audit bindings for authorized coding.

Adapts the workflow's in-memory approval store and the existing audit log
into the workflow's decision trail. Every decision is recorded with the
actor, the resource (workspace root + path), the decision, and a
redacted payload. The redaction is applied here, so the audit trail never
contains secret values.
"""

from __future__ import annotations

from . import redaction
from .models import AuditDecision, AuditEvent

__all__ = ["ActionAudit", "AuditRecordStore"]


class AuditRecordStore:
    """Small append-only record store used when no external audit log is
    injected. The production workflow wires this to the existing
    :class:`aura.security.audit.AuditLog`."""

    def __init__(self) -> None:
        self._records: list[AuditEvent] = []

    def record(self, *, action, actor, resource, decision, reason, event_id, correlation_id=None, payload=None) -> AuditEvent:
        event = AuditEvent(
            action=action,
            actor=actor,
            resource=resource,
            decision=decision,
            reason=reason,
            event_id=event_id,
            correlation_id=correlation_id,
            payload=dict(payload or {}),
        )
        self._records.append(event)
        return event

    @property
    def records(self) -> list[AuditEvent]:
        return list(self._records)


class ActionAudit:
    """Tracks authorized-coding decisions and writes them into an audit log."""

    def __init__(self, log=None, *, redactor=None) -> None:
        self._store = AuditRecordStore() if log is None else log
        self._redactor = redactor or redaction.SecretRedactor()

    @classmethod
    def from_aura_log(cls, audit_log: object) -> "ActionAudit":
        """Build an audit adapter wired to the existing :class:`AuditLog`
        (from ``aura.security.audit``). The adapter leaves the log
        completely untouched otherwise.

        .. code:: python

            from aura.security.audit import AuditLog, audit_log
            audit = ActionAudit.from_aura_log(audit_log())
        """
        return cls(log=audit_log)

    @property
    def records(self) -> list[AuditEvent]:
        return self._store.records

    def record(
        self,
        *,
        action: str,
        actor: str,
        resource: str,
        decision: AuditDecision,
        reason: str,
        event_id: str,
        correlation_id: str | None = None,
        payload: dict[str, object] | None = None,
        **extra: object,
    ) -> AuditEvent:
        """Record one decision with secrets redacted."""
        sanitized = redaction.redact_payload(payload or {}, self._redactor)
        merged = dict(sanitized)
        merged.update(extra)
        return self._store.record(
            action=action,
            actor=actor,
            resource=resource,
            decision=decision.value,
            reason=reason,
            event_id=event_id,
            correlation_id=correlation_id,
            payload=merged,
        )
