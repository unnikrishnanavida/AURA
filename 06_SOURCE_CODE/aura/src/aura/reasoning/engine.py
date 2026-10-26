"""Reasoning engine.

Executes the enabled strategies against one input, verifies the outcome,
computes consensus, and returns a structured, traceable ReasoningResult.
Uncertainty-first: with insufficient evidence the answer is "I do not know".
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any, cast

from aura.providers.handoff import build_provider_messages
from aura.providers.result import ProviderStatus
from aura.reasoning.abductive import AbductiveStrategy
from aura.reasoning.analogical import AnalogicalStrategy
from aura.reasoning.causal import CausalStrategy
from aura.reasoning.consensus import ConsensusEngine, ConsensusVerdict
from aura.reasoning.counterfactual import CounterfactualStrategy
from aura.reasoning.deductive import DeductiveStrategy
from aura.reasoning.grounding import build_grounded_conclusion
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

# Strategies that always participate. The remaining strategies are selected
# on task context — counterfactual requires hypotheses, analogical requires
# base cases. Selecting by evidence keeps the reasoning pass focused without
# ever dropping the deterministic core (REAS-1).
_CORE_STRATEGIES = ("deductive", "abductive", "causal", "probabilistic")


@dataclass(frozen=True)
class ReasoningResult:
    question: str
    conclusions: tuple[Conclusion, ...]
    verdict: ConsensusVerdict
    verification: VerificationResult
    trace: ReasoningTrace
    answer: str
    confidence: float | None
    uncertainty: UncertaintyLevel | None
    provider_name: str | None = None
    provider_synthesized: bool = False
    provider_mode: str | None = None
    #: Canonical provider outcome (``ok``, ``not_configured``, ``timeout``, ...).
    #: ``None`` means no provider was consulted at all.
    provider_status: str | None = None
    provider_model: str | None = None
    provider_local: bool | None = None
    #: Always False for model output: a provider answer is an input to
    #: verification, never a verified result.
    provider_verified: bool = False
    #: When ``provider_status`` is ``cancelled``, the canonical stage at which
    #: cancellation was observed (``provider.dispatch`` / ``provider.http`` /
    #: ``provider`` / ``provider.after_response``). ``None`` otherwise.
    provider_cancelled_stage: str | None = None
    #: Why AURA declined to answer, when it declined. Gives the caller something
    #: honest and specific to show instead of a bare "I do not know".
    abstention_reason: str | None = None
    strategies_selected: tuple[str, ...] = ()
    grounded: bool = False
    grounding_used: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty.value if self.uncertainty is not None else None,
            "verification": self.verification.to_dict(),
            "trace": self.trace.lines(),
            "conclusions": [c.to_dict() for c in self.conclusions],
            "strategies": list(self.strategies_selected),
            "grounded": self.grounded,
        }
        if self.grounding_used:
            payload["grounding_used"] = list(self.grounding_used)
        if self.abstention_reason is not None:
            payload["abstention_reason"] = self.abstention_reason
        if self.provider_status is not None:
            payload["provider_status"] = self.provider_status
        if self.provider_name is not None:
            provider = {
                "name": self.provider_name,
                "synthesized": self.provider_synthesized,
            }
            if self.provider_mode == "generation":
                provider["mode"] = "generation"
            if self.provider_status == ProviderStatus.CANCELLED.value and self.provider_cancelled_stage is not None:
                provider["cancelled_stage"] = self.provider_cancelled_stage
            payload["provider"] = provider
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

    def select_strategies(self, inp: ReasoningInput) -> tuple[str, ...]:
        """Choose which enabled strategies apply to this task context and evidence.

        Selection is deterministic and evidence-aware:

        - the core four strategies always participate;
        - ``counterfactual`` participates only when hypotheses are supplied
          (with no hypotheses there is nothing to vary counterfactually);
        - ``analogical`` participates only when base cases are supplied (with
          no cases there is nothing to reason from analogy).

        The returned tuple is ordered by the engine's canonical strategy order.
        """
        selected = [
            name
            for name in _CORE_STRATEGIES
            if name in self._enabled
        ]
        if inp.hypotheses and "counterfactual" in self._enabled:
            selected.append("counterfactual")
        if inp.cases and "analogical" in self._enabled:
            selected.append("analogical")
        return tuple(name for name in self._enabled if name in selected)

    def reason(
        self,
        inp: ReasoningInput,
        *,
        history: Sequence[dict[str, str]] = (),
        provider_authorized: bool = True,
        cancellation: Any = None,
    ) -> ReasoningResult:
        conclusions: list[Conclusion] = []
        trace = ReasoningTrace(assumptions=list(inp.assumptions))
        selected = self.select_strategies(inp)

        # Retrieved context enters the fact base *before* the strategies run, so
        # rules, base cases and Bayesian evidence can actually fire on what was
        # remembered or already known. Caller-supplied facts always win: an
        # explicit assertion is never overwritten by a retrieved one.
        effective = inp
        grounding_facts = inp.grounding.facts()
        if grounding_facts:
            merged = dict(grounding_facts)
            merged.update(inp.facts)
            effective = replace(inp, facts=merged)

        for name in selected:
            conclusion = self._strategy(name).reason(effective)
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
        # Verification sees the effective fact base so retrieved knowledge can
        # contest a derived conclusion (rather than being ignored), and the
        # grounded fallback can be verified on its own merits.
        verification = self._verification.verify(primary, effective, trace)
        confidence = primary.confidence
        uncertainty = uncertainty_from_confidence(confidence)
        grounded = False
        grounding_used: tuple[str, ...] = ()
        abstention_reason: str | None = None
        provider_status: str | None = None

        if verification.status == "contested":
            answer = f"CONTESTED: {verification.reason}"
            confidence = 0.0
            uncertainty = UncertaintyLevel.HIGH
        elif verification.status == "insufficient" or verdict.agreement == "uncertain" or effective.observed_propositions and len(effective.observed_propositions) < effective.min_evidence:
            # The deterministic pass declined. Before abstaining entirely, try
            # to answer *from retrieved context* -- extractively, attributed,
            # and only from items that cleared the belief floor.
            grounded_conclusion = build_grounded_conclusion(
                items=inp.grounding.items,
                contradictions=inp.grounding.contradictions,
            )
            if grounded_conclusion is not None:
                answer = grounded_conclusion.statement
                confidence = grounded_conclusion.confidence
                uncertainty = uncertainty_from_confidence(confidence)
                grounded = True
                grounding_used = tuple(item.reference for item in inp.grounding.items)
            else:
                answer = "I do not know"
                confidence = 0.0
                uncertainty = UncertaintyLevel.HIGH
                if self._provider_manager is None:
                    # Nothing can generate on this deployment. Say so plainly so
                    # the caller learns AURA is reasoning locally and lacks a
                    # language model, rather than that it has no information.
                    abstention_reason = (
                        "AURA can reason over saved memory and stored knowledge, but no "
                        "language model is currently configured for broader generation."
                    )
                    # Report it in the same vocabulary as every other provider
                    # outcome, so a caller never has to infer the difference
                    # between "no provider" and "provider was never consulted".
                    provider_status = ProviderStatus.NOT_CONFIGURED.value
        else:
            answer = verdict.answer or primary.statement

        # Phase 29 provider boundary: safe structured synthesis. Only when (a) a
        # provider manager is configured AND (b) the deterministic outcome is
        # evidence-supported (never override contested / insufficient / uncertain
        # results, which are authoritative for uncertainty-first reasoning).
        provider_name: str | None = None
        provider_synthesized = False
        provider_mode: str | None = None
        provider_model: str | None = None
        provider_local: bool | None = None
        provider_verified = False
        provider_cancelled_stage: str | None = None
        if self._provider_manager is not None and self._may_synthesize(verification, verdict, inp):
            synthesized = self._provider_manager.synthesize(
                question=inp.question,
                conclusions=tuple(conclusions),
                verification=verification.to_dict() if hasattr(verification, "to_dict") else str(verification),
                cancellation=cancellation,
            )
            if synthesized:
                answer = synthesized
                provider_name = self._provider_manager.last_provider
                provider_synthesized = True
                provider_mode = "synthesis"
            elif cancellation is not None and cancellation.cancelled:
                # The provider path was interrupted (or never dispatched): the
                # deterministic answer is kept, and the cancellation is reported
                # honestly in the provider vocabulary.
                provider_status = ProviderStatus.CANCELLED.value
                provider_cancelled_stage = "provider"
                if getattr(self._provider_manager, "last_provider", None):
                    provider_name = self._provider_manager.last_provider
                    provider_mode = "synthesis"
                abstention_reason = "cancelled before or during provider synthesis"
        elif self._provider_manager is not None and answer == "I do not know" and verification.status != "contested":
            # Grounding and deterministic reasoning were not enough. Ask an
            # authorized provider, handing it the Step 1A context -- never a
            # second, privately-assembled retrieval.
            messages = build_provider_messages(
                question=inp.question,
                grounding=inp.grounding,
                history=tuple(history),
            )
            result = self._provider_manager.generate(
                question=inp.question,
                history=tuple(history),
                messages=messages,
                authorized=provider_authorized,
                cancellation=cancellation,
            )
            provider_status = result.status.value
            provider_model = result.model
            provider_local = result.local
            if result.ok:
                answer = result.text or ""
                provider_name = result.provider
                provider_mode = "generation"
                # A generated answer is never promoted to verified truth: the
                # deterministic confidence/uncertainty stay unset and the
                # verification status records that no check has been performed.
                provider_verified = False
            else:
                abstention_reason = result.error
                provider_cancelled_stage = result.cancelled_stage

        return ReasoningResult(
            question=inp.question,
            conclusions=tuple(conclusions),
            verdict=verdict,
            verification=verification,
            trace=trace,
            answer=answer,
            confidence=round(confidence, 6) if provider_mode != "generation" else None,
            uncertainty=uncertainty if provider_mode != "generation" else None,
            provider_name=provider_name,
            provider_synthesized=provider_synthesized,
            provider_mode=provider_mode,
            provider_status=provider_status,
            provider_model=provider_model,
            provider_local=provider_local,
            provider_verified=provider_verified,
            provider_cancelled_stage=provider_cancelled_stage,
            abstention_reason=abstention_reason,
            strategies_selected=selected,
            grounded=grounded,
            grounding_used=grounding_used,
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