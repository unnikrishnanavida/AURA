"""Embedded deterministic reasoning provider.

Runs AURA's built-in multi-strategy reasoning locally with zero network
dependencies. This is the default provider: reproducible, private, offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aura.providers.base import Provider, ProviderProfile


@dataclass
class EmbeddedReasoningProvider(Provider):
    """Adapter exposing the reasoning engine behind the provider contract.

    This adapter deliberately does NOT claim ``reasoning.synthesis``: the
    embedded provider IS the multi-strategy reasoner, so the manager never
    routes synthesis back into it (that would recurse). It is always registered
    so registry discovery/health work without any remote credentials.
    """

    profile: ProviderProfile = ProviderProfile(
        name="embedded",
        kind="reasoning",
        capabilities=("reasoning.multi_strategy", "reasoning.deterministic"),
        latency_ms=1.0,
        cost_per_call=0.0,
        reliability=1.0,
        local=True,
        privacy_approved=True,
    )
    timeout_seconds: float = 30.0

    def __init__(self, seed: int | None = None) -> None:
        from aura.reasoning.engine import ReasoningEngine

        self._engine = ReasoningEngine(seed=seed)
        self.seed = seed

    def health(self) -> bool:
        return True

    def reason(self, question: str, **kwargs: Any) -> Any:
        from aura.reasoning.engine import ReasoningInput

        rules = tuple(kwargs.pop("rules", ()))
        hypotheses = tuple(kwargs.pop("hypotheses", ()))
        likelihoods = dict(kwargs.pop("likelihoods", {}))
        facts = dict(kwargs.pop("facts", {}))
        cases = tuple(kwargs.pop("cases", ()))
        inp = ReasoningInput(
            question=question,
            facts=facts,
            rules=rules,
            hypotheses=hypotheses,
            likelihoods=likelihoods,
            prior=float(kwargs.pop("prior", 0.5)),
            cases=cases,
        )
        return self._engine.reason(inp)


__all__ = ["EmbeddedReasoningProvider"]