"""Approval policy: translates autonomy mode + risk into an approval gate."""

from __future__ import annotations

from dataclasses import dataclass

from aura_agent.autonomy.modes.autonomy_mode import AutonomyMode

__all__ = ["ApprovalDecision", "ApprovalPolicy"]


@dataclass(frozen=True)
class ApprovalDecision:
    """Whether approval is required and why."""

    required: bool
    reason: str


class ApprovalPolicy:
    """Single deterministic decision procedure for approval requirements.

    The approval policy is *composed* with safety REVIEW and constitution
    REVIEW verdicts upstream; this policy only decides the autonomy-based
    approval gate.
    """

    def evaluate(self, *, mode: AutonomyMode, risk_score: float) -> ApprovalDecision:
        if risk_score >= AutonomyMode.human_required_threshold():
            return ApprovalDecision(
                required=True,
                reason=f"risk {risk_score:g} exceeds the universal human-approval ceiling",
            )
        if mode.allows(risk_score=risk_score):
            return ApprovalDecision(
                required=False,
                reason=f"autonomy mode {mode.name} permits risk {risk_score:g}",
            )
        return ApprovalDecision(
            required=True,
            reason=f"autonomy mode {mode.name} requires approval for risk {risk_score:g}",
        )