"""Privacy engineering controls.

- classification against :class:`aura.memory.models.Sensitivity`;
- policy-driven redaction of structured payloads (logs, metrics, traces,
  audit, prompts, provider calls) by field allowlist;
- retention enforcement (expiry checks and deletion for sensitive records);
- purge planning (safe deletion instructions, no destructive surprises).

This module is a *control layer*: it never transports, logs, or forwards data
itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aura.memory.models import Sensitivity


class RetentionDecision(StrEnum):
    KEEP = "keep"
    EXPIRE = "expire"
    REQUIRES_DELETION = "requires_deletion"


@dataclass(frozen=True)
class RedactionPolicy:
    """Which top-level payload fields survive privacy redaction."""

    allow: tuple[str, ...] = ()


@dataclass
class PrivacyResult:
    redacted: dict[str, Any]
    dropped_fields: tuple[str, ...] = ()


class PrivacyGate:
    """Classification + redaction + retention control surface."""

    def __init__(self, *, redaction_policy: RedactionPolicy | None = None) -> None:
        self._policy = redaction_policy or RedactionPolicy()

    def classify(self, *, sensitivity: Sensitivity | str) -> Sensitivity:
        if isinstance(sensitivity, Sensitivity):
            return sensitivity
        return Sensitivity(sensitivity)

    def redact(self, payload: dict[str, Any], *, sensitivity: Sensitivity | str) -> PrivacyResult:
        """Redact a structured payload by allowlist.

        Non-sensitive payloads (PUBLIC) pass through unchanged; anything
        sensitive is reduced to the allowed fields or emptied.
        """
        sev = self.classify(sensitivity=sensitivity)
        if sev is Sensitivity.PUBLIC:
            return PrivacyResult(redacted=dict(payload), dropped_fields=())
        dropped = tuple(field_name for field_name in payload if field_name not in self._policy.allow)
        kept = {k: v for k, v in payload.items() if k not in dropped}
        return PrivacyResult(redacted=kept, dropped_fields=dropped)

    def retention(self, *, expires_at: Any, now: Any) -> RetentionDecision:
        """Decide expiry from an ISO/datetime ``expires_at`` vs ``now``."""
        if expires_at is None:
            return RetentionDecision.KEEP
        try:
            if _as_timestamp(expires_at) <= _as_timestamp(now):
                return RetentionDecision.EXPIRE
        except (TypeError, ValueError):
            return RetentionDecision.REQUIRES_DELETION
        return RetentionDecision.KEEP

    @staticmethod
    def purge_note(records: int, *, context: str = "memory") -> str:
        """Human-readable, operationally safe purge guidance (no auto-delete)."""
        return (
            f"purge {records} {context} record(s): archive or delete via the "
            "storage API with an explicit operator-approved command"
        )


def _as_timestamp(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    from datetime import datetime

    if isinstance(value, datetime):
        return value.timestamp()
    from datetime import datetime as dt

    return dt.fromisoformat(str(value)).timestamp()


__all__ = ["PrivacyGate", "PrivacyResult", "RedactionPolicy", "RetentionDecision"]