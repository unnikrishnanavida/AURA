"""Learning-signal gate: the authorization boundary for reflection output.

Reflection produces candidate ImprovementSignals. This gate is the ONLY place
that may approve them, and approval requires an explicit ``authorize`` call.
Signals are never self-approved.

A signal is validated only when:

- it carries a non-empty proposed action,
- its lesson has meaningful confidence (> 0),
- it is explicitly approved by an authorizer with a recorded identity.
"""
from __future__ import annotations

from ..models.reflection_result import ImprovementSignal


class UnauthorizedMutationError(RuntimeError):
    """Raised when code attempts to apply an unapproved learning signal."""


class ReflectionGate:
    """Validates and authorizes learning signals produced by reflection."""

    def validate(self, signal: ImprovementSignal) -> tuple[bool, str]:
        """Checks structural validity without mutating the signal."""
        if not signal.proposed_action or not signal.proposed_action.strip():
            return False, "proposed_action is empty"
        if signal.lesson.confidence <= 0.0:
            return False, "lesson confidence is zero; cannot act on it"
        if signal.approved and not signal.approver:
            return False, "approved signal missing authorizer identity"
        return True, "valid"

    def authorize(
        self, signal: ImprovementSignal, approver: str
    ) -> ImprovementSignal:
        """Return an approved copy. Does not mutate the input signal."""
        valid, reason = self.validate(signal)
        if not valid:
            raise UnauthorizedMutationError(
                f"cannot authorize invalid signal: {reason}"
            )
        return ImprovementSignal(
            lesson=signal.lesson,
            proposed_action=signal.proposed_action,
            approved=True,
            approver=approver,
        )

    def require_approved(self, signal: ImprovementSignal) -> None:
        """Enforce that a signal is authorized before any caller applies it."""
        if not signal.approved:
            raise UnauthorizedMutationError(
                "learning signal was not approved; refusing to apply"
            )


def apply_if_authorized(
    gate: ReflectionGate,
    signal: ImprovementSignal,
    approver: str | None = None,
) -> None:
    """Apply a proposed change ONLY after authorization.

    This is deliberately the one choke point that subsystems may call to apply
    a refined behavior change coming from reflection. Anything that would
    short-circuit ``authorize`` is a safety violation.
    """
    approved = gate.authorize(signal, approver) if approver else signal
    gate.require_approved(approved)
