"""Autonomy.

Autonomy modes range MANUAL -> ASSISTED -> SUPERVISED -> AUTONOMOUS. Higher
autonomy only raises the risk threshold that may auto-approve; it never
converts a safety or permission DENY into an ALLOW.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AutonomyMode(StrEnum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"


class AutonomousDecision(StrEnum):
    APPROVED = "approved"
    REQUIRES_APPROVAL = "requires_approval"


_RISK_CEILINGS = {
    AutonomyMode.MANUAL: 0.0,
    AutonomyMode.ASSISTED: 0.2,
    AutonomyMode.SUPERVISED: 0.5,
    AutonomyMode.AUTONOMOUS: 1.0,
}


@dataclass(frozen=True)
class AutonomyResult:
    decision: AutonomousDecision
    reason: str


class AutonomyGate:
    def __init__(self, initial_mode: AutonomyMode = AutonomyMode.SUPERVISED) -> None:
        self.mode = initial_mode

    def evaluate(self, risk: float, *, authorization_held: bool = False) -> AutonomyResult:
        ceiling = _RISK_CEILINGS[self.mode]
        if risk <= ceiling or authorization_held:
            return AutonomyResult(AutonomousDecision.APPROVED, f"autonomy {self.mode.value} approves risk {risk:.2f}")
        return AutonomyResult(
            AutonomousDecision.REQUIRES_APPROVAL,
            f"risk {risk:.2f} exceeds autonomy ceiling {ceiling:.2f} for {self.mode.value}; approval required",
        )


__all__ = ["AutonomousDecision", "AutonomyGate", "AutonomyMode"]