"""Learning signal validation gate.

Observation -> candidate signal -> validation -> approved signal -> controlled
update. The gate rejects signals with insufficient evidence and blocks any
safety-relevant change without explicit authorization.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.learning.models import LearningSignal


@dataclass(frozen=True)
class ValidationOutcome:
    approved: bool
    reason: str
    score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {"approved": self.approved, "reason": self.reason, "score": self.score}


class SignalValidator:
    def __init__(
        self,
        *,
        min_evidence_count: int = 1,
        min_evidence_score: float = 0.0,
        authorize_safety_relevant: bool = False,
    ) -> None:
        self.min_evidence_count = min_evidence_count
        self.min_evidence_score = min_evidence_score
        self.authorize_safety_relevant = authorize_safety_relevant

    def validate(self, signal: LearningSignal) -> ValidationOutcome:
        if signal.status.value == "rejected":
            return ValidationOutcome(False, "signal already rejected")

        if len(signal.evidence) < self.min_evidence_count:
            return ValidationOutcome(
                False,
                f"insufficient evidence: {len(signal.evidence)} < {self.min_evidence_count}",
            )

        total = sum(evidence.get("score", 0.0) for evidence in signal.evidence)
        average = total / len(signal.evidence)
        if average < self.min_evidence_score:
            return ValidationOutcome(
                False, f"evidence score {average:.2f} below threshold {self.min_evidence_score}"
            )

        if signal.safety_relevant and not (signal.authorized or self.authorize_safety_relevant):
            return ValidationOutcome(
                False,
                "safety-relevant learning signal blocked until explicit authorization; "
                "AURA never auto-amends safety policy",
            )

        return ValidationOutcome(True, "signal validated; safe to apply", score=round(average, 6))


__all__ = ["SignalValidator", "ValidationOutcome"]