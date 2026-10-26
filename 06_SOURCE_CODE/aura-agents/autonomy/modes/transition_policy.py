"""Autonomy transition policy: which mode changes are allowed."""

from __future__ import annotations

from aura_agent.autonomy.modes.autonomy_mode import AutonomyMode
from aura_agent.contracts.errors import InvalidStateTransition

__all__ = ["AutonomyTransitionPolicy"]


class AutonomyTransitionPolicy:
    """Governs legal autonomy-mode transitions.

    Escalation of autonomy requires an authorizing entity; de-escalation is
    always allowed (an agent may always reduce its own autonomy, and safety
    systems may force it).
    """

    @staticmethod
    def allowed(source: AutonomyMode, target: AutonomyMode, *, authorized_by: str | None) -> bool:
        if source is target:
            return True
        # decreasing autonomy is always legal
        if target < source:
            return True
        return authorized_by is not None

    def transition(
        self,
        source: AutonomyMode,
        target: AutonomyMode,
        *,
        authorized_by: str | None,
    ) -> AutonomyMode:
        if not self.allowed(source, target, authorized_by=authorized_by):
            raise InvalidStateTransition(
                source.name,
                target.name,
                details={"reason": "autonomy escalation requires authorization"},
            )
        return target
