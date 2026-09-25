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
    provider_name: str | None = None
    provider_synthesized: bool = False

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty.value,
            "verification": self.verification.to_dict(),
            "trace": self.trace.lines(),
            "conclusions": [c.to_dict() for c in self.conclusions],
        }
        if self.provider_name is not None:
            payload["provider"] = {
                "name": self.provider_name,
                "synthesized": self.provider_synthesized,
            }
        return payload


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
        provider_manager: Any | None = None,
    ) -> None:
        del seed  # reproducibility handled by SeededRandom; strategies are deterministic
        unknown = [name for name in enabled if name not in _STRATEGIES]
        if unknown:
            raise ValueError(f"unknown reasoning strategies: {unknown}")
        self._enabled = enabled
        self._consensus = ConsensusEngine()
        self._verification = VerificationEngine()
        self._similarity_threshold = similarity_threshold
        # Phase 29: optional provider boundary for final safe synthesis.
        # Never set by default — the deterministic path is preserved.
        self._provider_manager = provider_manager

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

        # Phase 29 provider boundary: safe structured synthesis. Only when (a) a
        # provider manager is configured AND (b) the deterministic outcome is
        # evidence-supported (never override contested / insufficient / uncertain
        # results, which are authoritative for uncertainty-first reasoning).
        provider_name: str | None = None
        provider_synthesized = False
        if self._provider_manager is not None and self._may_synthesize(verification, verdict, inp):
            synthesized = self._provider_manager.synthesize(
                question=inp.question,
                conclusions=tuple(conclusions),
                verification=verification.to_dict() if hasattr(verification, "to_dict") else str(verification),
            )
            if synthesized:
                answer = synthesized
                provider_name = self._provider_manager.last_provider
                provider_synthesized = True

        return ReasoningResult(
            question=inp.question,
            conclusions=tuple(conclusions),
            verdict=verdict,
            verification=verification,
            trace=trace,
            answer=answer,
            confidence=round(confidence, 6),
            uncertainty=uncertainty,
            provider_name=provider_name,
            provider_synthesized=provider_synthesized,
        )

    @staticmethod
    def _may_synthesize(verification: Any, verdict: Any, inp: Any) -> bool:
        """True only when an evidence-supported outcome may be polished by a provider."""
        observed = getattr(inp, "observed_propositions", None)
        return not (
            getattr(verification, "status", "confirmed") in {"contested", "insufficient"}
            or getattr(verdict, "agreement", None) == "uncertain"
            or (
                observed
                and len(observed) < int(getattr(inp, "min_evidence", 0) or 0)
            )
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