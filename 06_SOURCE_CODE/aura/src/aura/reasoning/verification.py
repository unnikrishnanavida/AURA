"""Verification.

Checks a conclusion against the supporting evidence: whether the answer should
be verified, contested, or flagged insufficient.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.reasoning.models import Conclusion, ReasoningInput, ReasoningTrace
from aura.reasoning.uncertainty import uncertainty_from_confidence

# keep uncertainty_from_confidence import used for API parity
_USED_UNUSED_MARK = uncertainty_from_confidence  # noqa: F841


@dataclass(frozen=True)
class VerificationResult:
    status: str  # verified | contested | insufficient
    reason: str
    conclusion: Conclusion

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "reason": self.reason}


_NEGATIONS = ("not ", "no ", "never", "cannot", "without", "lack of")


class VerificationEngine:
    def verify(
        self, conclusion: Conclusion, inp: ReasoningInput, trace: ReasoningTrace
    ) -> VerificationResult:
        if conclusion.confidence <= 0.0:
            return VerificationResult(
                "insufficient",
                "conclusion carries no confidence; AURA declines to assert it",
                conclusion,
            )

        for proposition, belief in inp.facts.items():
            if (
                belief >= 0.7
                and _subjects_overlap(proposition, conclusion.statement)
                and _opposite_polarity(proposition, conclusion.statement)
            ):
                return VerificationResult(
                    "contested",
                    f"conclusion contradicts observed fact {proposition!r}",
                    conclusion,
                )

        if len(trace.steps) == 0 and not conclusion.supports:
            return VerificationResult(
                "insufficient", "conclusion has no recorded inference steps", conclusion
            )
        return VerificationResult("verified", "conclusion supported by recorded inference", conclusion)


def _subjects_overlap(proposition: str, statement: str) -> bool:
    subject = proposition.replace("not ", "").replace("no ", "").strip()
    if len(subject) < 3:
        return False
    return subject in statement.lower()


def _opposite_polarity(proposition: str, statement: str) -> bool:
    def negated(text: str) -> bool:
        lowered = text.lower()
        return any(lowered.startswith(token) or f" {token}" in f" {lowered}" for token in _NEGATIONS)

    return negated(proposition) != negated(statement)


__all__ = ["VerificationEngine", "VerificationResult"]