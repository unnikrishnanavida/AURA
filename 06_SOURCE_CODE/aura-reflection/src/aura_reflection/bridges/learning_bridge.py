"""Learning-signal bridge: the ONLY path from reflection into learning.

Reflection produces candidate ImprovementSignals. This bridge converts a
gate-approved signal into a concrete :class:`LearningSignal` that the learning
subsystem may consume. It never applies anything; it never bypasses the gate;
and applying a learning signal requires an explicit authorized call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from aura_reflection.models.reflection_result import ImprovementSignal
from aura_reflection.services.reflection_gate import (
    ReflectionGate,
    UnauthorizedMutationError,
)

# Patterns that commonly precede secrets; values following them are masked so
# sensitive material never appears in learning signals or logs.
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(sk-[A-Za-z0-9_-]{6,})", re.IGNORECASE), "<redacted-secret>"),
    (re.compile(r"(api[_-]?key\s*[=:]\s*[A-Za-z0-9_-]{6,})", re.IGNORECASE), "api_key=<redacted>"),
    (re.compile(r"(token\s*[=:]\s*[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "token=<redacted>"),
    (re.compile(r"(bearer\s+[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "bearer <redacted>"),
    (re.compile(r"(password\s*[=:]\s*\S+)", re.IGNORECASE), "password=<redacted>"),
)


def redact(text: str) -> str:
    """Mask secret-like substrings in a piece of text."""
    out = text
    for pattern, replacement in _SECRET_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class LearningSignal:
    """A validated, approved learning signal ready for the learning subsystem.

    All free-text fields are redacted at construction so secrets never leak.
    """

    signal_id: str
    lesson: str
    lesson_confidence: float
    proposed_action: str
    approver: str
    signal_kind: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "lesson", redact(self.lesson))
        object.__setattr__(self, "proposed_action", redact(self.proposed_action))

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "lesson": self.lesson,
            "lesson_confidence": self.lesson_confidence,
            "proposed_action": self.proposed_action,
            "approver": self.approver,
            "signal_kind": self.signal_kind,
            "created_at": self.created_at.isoformat(),
        }


class LearningSignalBroker:
    """Packages approved reflection signals into learning signals."""

    def __init__(self, gate: ReflectionGate | None = None) -> None:
        self.gate = gate or ReflectionGate()

    def package(self, signal: ImprovementSignal) -> LearningSignal:
        """Wrap a gate-approved signal into a LearningSignal.

        Refuses to package signals that are not explicitly approved: an
        unapproved signal must never enter the learning path.
        """
        self.gate.require_approved(signal)
        return LearningSignal(
            signal_id=str(uuid4()),
            lesson=signal.lesson.summary,
            lesson_confidence=signal.lesson.confidence,
            proposed_action=signal.proposed_action,
            approver=signal.approver or "unknown",
            signal_kind=f"improvement:{signal.lesson.category}",
            created_at=utcnow(),
        )

    def apply_if_authorized(
        self,
        learning_signal: LearningSignal,
        *,
        apply_fn,
    ) -> object:
        """Apply a learning signal only through an explicit apply callable.

        ``apply_fn`` receives the learning signal and is fully responsible for
        the actual mutation. This method is the choke point that proves the
        caller is invoking the apply path deliberately; it never applies
        anything itself.
        """
        if not learning_signal.approver:
            raise UnauthorizedMutationError(
                "learning signal has no recorded authorizer; refusing to apply"
            )
        return apply_fn(learning_signal)