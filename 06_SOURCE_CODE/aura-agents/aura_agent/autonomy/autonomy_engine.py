"""Autonomy engine: owns the current autonomy mode and approval decisions."""

from __future__ import annotations

from aura_agent.autonomy.modes.autonomy_mode import AutonomyMode
from aura_agent.autonomy.modes.transition_policy import AutonomyTransitionPolicy
from aura_agent.autonomy.policies.approval_policy import (
    ApprovalDecision,
    ApprovalPolicy,
)

__all__ = ["AutonomyEngine"]


class AutonomyEngine:
    """Holds the current mode and answers approval questions.

    The engine never decides safety, permission, capability, or constitution
    matters; it only decides *whether human approval is required* for an action
    that has already passed those hard checks.
    """

    def __init__(
        self,
        initial_mode: AutonomyMode = AutonomyMode.SUPERVISED,
        transition_policy: AutonomyTransitionPolicy | None = None,
        approval_policy: ApprovalPolicy | None = None,
    ) -> None:
        self._mode = initial_mode
        self._transitions = transition_policy or AutonomyTransitionPolicy()
        self._approvals = approval_policy or ApprovalPolicy()

    def mode(self) -> AutonomyMode:
        return self._mode

    def switch_mode(
        self, target: AutonomyMode, *, authorized_by: str | None = None
    ) -> AutonomyMode:
        self._mode = self._transitions.transition(
            self._mode, target, authorized_by=authorized_by
        )
        return self._mode

    def requires_approval(self, *, risk_score: float, action_name: str) -> ApprovalDecision:
        """Query the approval gate for an action at ``risk_score``."""
        return self._approvals.evaluate(mode=self._mode, risk_score=risk_score)

    def can_self_escalate(self) -> bool:
        """Whether an unauthed agent may raise its own autonomy."""
        return False