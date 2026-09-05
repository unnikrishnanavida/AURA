"""Learning engine: the safe learning pipeline.

submit -> validate -> approve -> controlled apply -> registry (rollback-able).
Learning never mutates security/safety/permission policy without explicit
authorization, enforced by the validation gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.learning.gate import SignalValidator, ValidationOutcome
from aura.learning.models import LearningSignal, SignalStatus
from aura.learning.registry import AppliedChange, LearningRegistry


@dataclass
class LearningResult:
    signal: LearningSignal
    outcome: ValidationOutcome
    change: AppliedChange | None = None

    @property
    def applied(self) -> bool:
        return self.change is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "signal": self.signal.to_dict(),
            "outcome": self.outcome.to_dict(),
            "applied_ref": self.change.ref if self.change else None,
        }


class LearningEngine:
    def __init__(
        self,
        *,
        validator: SignalValidator | None = None,
        registry: LearningRegistry | None = None,
    ) -> None:
        self.validator = validator or SignalValidator()
        self.registry = registry or LearningRegistry()

    def submit(self, signal: LearningSignal) -> LearningResult:
        outcome = self.validator.validate(signal)
        if not outcome.approved:
            signal.status = SignalStatus.REJECTED
            return LearningResult(signal=signal, outcome=outcome)
        signal.status = SignalStatus.APPROVED
        change = self.registry.apply(signal)
        return LearningResult(signal=signal, outcome=outcome, change=change)

    def approve_and_apply(self, signal: LearningSignal, *, authorized: bool = True) -> LearningResult:
        signal.authorized = authorized
        return self.submit(signal)

    def rollback(self, ref: str) -> AppliedChange:
        return self.registry.rollback(ref)

    def health(self) -> dict[str, object]:
        return {"status": "ok", "active_changes": len(self.registry.active())}


__all__ = ["LearningEngine", "LearningResult"]