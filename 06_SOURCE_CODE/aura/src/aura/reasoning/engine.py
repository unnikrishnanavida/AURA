"""Reasoning engine.

Executes the enabled strategies against one input, verifies the outcome,
computes consensus, and returns a structured, traceable ReasoningResult.
Uncertainty-first: with insufficient evidence the answer is "I do not know".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from aura.reasoning.abductive import AbductiveStrategy
from aura.reasoning.analogical import AnalogicalStrategy
from aura.reasoning.causal import CausalStrategy
from aura.reasoning.consensus import ConsensusEngine, ConsensusVerdict
from aura.reasoning.counterfactual import CounterfactualStrategy
from aura.reasoning.deductive import DeductiveStrategy
from aura.reasoning.models import (
    Conclusion,
    InferenceStep,
    ReasoningInput,
    ReasoningTrace,
    make_conclusion,
)
from aura.reasoning.probabilistic import BayesianStrategy
from aura.reasoning.uncertainty import UncertaintyLevel, uncertainty_from_confidence
from aura.reasoning.verification import VerificationEngine, VerificationResult

_STRATEGIES = {
    "deductive": DeductiveStrategy,
    "abductive": AbductiveStrategy,
    "causal": CausalStrategy,
    "probabilistic": BayesianStrategy,
    "counterfactual": CounterfactualStrategy,
    "analogical": AnalogicalStrategy,
}


@dataclass(frozen=True)
class ReasoningResult:
    question: str
    conclusions: tuple[Conclusion, ...]
    verdict: ConsensusVerdict
    verification: VerificationResult
    trace: ReasoningTrace
    answer: str
    confidence: float
    uncertainty: UncertaintyLevel

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty.value,
            "verification": self.verification.to_dict(),
            "trace": self.trace.lines(),
            "conclusions": [c.to_dict() for c in self.conclusions],
        }


class ReasoningEngine:
    """Composes strategies with consensus and verification."""

    def __init__(
        self,
        *,
        enabled: tuple[str, ...] = (
            "deductive",
            "abductive",
            "causal",
            "probabilistic",
            "counterfactual",
            "analogical",
        ),
        seed: int | None = None,
        similarity_threshold: float = 0.3,
    ) -> None:
        del seed  # reproducibility handled by SeededRandom in providers; strategies are deterministic
        unknown = [name for name in enabled if name not in _STRATEGIES]
        if unknown:
            raise ValueError(f"unknown reasoning strategies: {unknown}")
        self._enabled = enabled
        self._consensus = ConsensusEngine()
        self._verification = VerificationEngine()
        self._similarity_threshold = similarity_threshold

    def _strategy(self, name: str) -> Any:
        if name == "analogical":
            return cast(Any, _STRATEGIES[name])(similarity_threshold=self._similarity_threshold)
        return _STRATEGIES[name]()

    def reason(self, inp: ReasoningInput) -> ReasoningResult:
        conclusions: list[Conclusion] = []
        trace = ReasoningTrace(assumptions=list(inp.assumptions))

        for name in self._enabled:
            conclusion = self._strategy(name).reason(inp)
            if isinstance(conclusion, Conclusion):
                conclusions.append(conclusion)

        verdict = self._consensus.decide(conclusions)
        primary = self._primary(conclusions, verdict)
        if not trace.steps:
            # Propagate the winning conclusion's rule-level support so the
            # reasoning trace is never empty for rule-driven strategies.
            for support in primary.supports:
                trace.steps.append(
                    InferenceStep(
                        rule_id=support,
                        from_propositions=(),
                        derived=primary.statement,
                        confidence=primary.confidence,
                    )
                )
        verification = self._verification.verify(primary, inp, trace)
        confidence = primary.confidence
        uncertainty = uncertainty_from_confidence(confidence)

        if verification.status == "contested":
            answer = f"CONTESTED: {verification.reason}"
            confidence = 0.0
            uncertainty = UncertaintyLevel.HIGH
        elif verification.status == "insufficient" or verdict.agreement == "uncertain" or inp.observed_propositions and len(inp.observed_propositions) < inp.min_evidence:
            answer = "I do not know"
        else:
            answer = verdict.answer or primary.statement

        return ReasoningResult(
            question=inp.question,
            conclusions=tuple(conclusions),
            verdict=verdict,
            verification=verification,
            trace=trace,
            answer=answer,
            confidence=round(confidence, 6),
            uncertainty=uncertainty,
        )

    @staticmethod
    def _primary(conclusions: list[Conclusion], verdict: ConsensusVerdict) -> Conclusion:
        if verdict.answer:
            for conclusion in conclusions:
                if verdict.answer in conclusion.statement:
                    return conclusion
        return max(
            conclusions,
            key=lambda c: c.confidence,
            default=make_conclusion(strategy="none", statement="unknown", confidence=0.0, reasoning=[]),
        )


__all__ = ["ReasoningEngine", "ReasoningInput", "ReasoningResult"]