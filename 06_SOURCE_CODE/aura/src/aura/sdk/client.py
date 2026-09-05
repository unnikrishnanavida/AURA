"""AURA public SDK.

The stable, pleasant integration surface:

    from aura import Aura

    aura = Aura()
    result = aura.reason("is production ready?")

The facade exposes only public behavior; internal engine wiring is opaque.
"""

from __future__ import annotations

from typing import Any

from aura.brain.engine import BrainEngine
from aura.config.settings import AuraConfig
from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import ExecutionId
from aura.memory.engine import MemoryQuery
from aura.memory.models import MemoryType
from aura.planning.models import Goal, Task
from aura.providers.base import ProviderProfile
from aura.providers.embedded import EmbeddedReasoningProvider


class Aura:
    """High-level API for the AURA integrated platform."""

    def __init__(
        self,
        *,
        config: AuraConfig | None = None,
        clock: Clock | None = None,
        seed: int | None = None,
        provider: EmbeddedReasoningProvider | None = None,
    ) -> None:
        self._config = config or AuraConfig()
        self._clock = clock or SystemClock()
        self._brain = BrainEngine.create(config=self._config, clock=self._clock, seed=seed)
        self._provider = provider or EmbeddedReasoningProvider(seed=seed)

    @property
    def brain(self) -> BrainEngine:
        return self._brain

    @property
    def config(self) -> AuraConfig:
        return self._config

    @property
    def provider(self) -> EmbeddedReasoningProvider:
        return self._provider

    @property
    def provider_profile(self) -> ProviderProfile:
        return self._provider.profile

    # -- cognition -----------------------------------------------------------
    def reason(
        self,
        question: str,
        *,
        facts: dict[str, float] | None = None,
        rules: tuple[Any, ...] = (),
        hypotheses: tuple[str, ...] = (),
        cases: tuple[Any, ...] = (),
        goal: Goal | None = None,
        tasks: list[Task] | None = None,
    ) -> dict[str, Any]:
        """Run the full cognitive cycle and return a structured answer."""
        result = self._brain.reason(
            question=question,
            facts=facts,
            rules=rules,
            hypotheses=hypotheses,
            cases=cases,
            goal=goal,
            tasks=tasks,
        )
        return result.summary()

    def plan(
        self, *, goal: Goal, tasks: list[Task]
    ) -> dict[str, Any]:
        from aura.planning.engine import PlanningEngine

        engine = PlanningEngine()
        result = engine.plan(goal=goal, tasks=tasks)
        if result.primary is None:
            return {"plan_created": False, "issues": list(result.issues), "steps": []}
        return {
            "plan_created": True,
            "plan_id": str(result.primary.id),
            "steps": result.primary.names,
            "risk": result.primary.risk.to_dict() if hasattr(result.primary.risk, "to_dict") else result.primary.risk.level,
        }

    def reflect(
        self,
        *,
        goal: str,
        success: bool,
        observed: dict[str, Any] | None = None,
        expected: dict[str, Any] | None = None,
        deviations: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        return self._brain.reflect_and_learn(
            goal=goal,
            success=success,
            observed=observed,
            expected=expected,
            deviations=deviations,
            metrics=metrics,
        ).summary()

    # -- memory ---------------------------------------------------------------
    def remember(
        self,
        key: str,
        content: dict[str, Any],
        *,
        kind: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
    ) -> str:
        entry = self._brain.memory.remember(key=key, kind=kind, content=content, importance=importance)
        return str(entry.id)

    def recall(self, text: str, *, limit: int = 5) -> list[dict[str, Any]]:
        entries = self._brain.memory.recall(MemoryQuery(text=text, limit=limit))
        return [
            {"id": str(e.id), "key": e.key, "kind": e.kind.value, "content": e.content}
            for e in entries
        ]

    # -- knowledge -------------------------------------------------------------
    def observe(self, *, statement: str, predicate: tuple[str, ...] = ()) -> str:
        from aura.knowledge.models import Claim

        claim = Claim.create(statement=statement, predicate=predicate)
        self._brain.knowledge.add(claim)
        return str(claim.id)

    def retrieve(
        self, *, predicate: tuple[str, ...] = (), statement: str = "", limit: int = 10
    ) -> list[dict[str, object]]:
        results = self._brain.knowledge.retrieve(predicate=predicate, statement=statement, limit=limit)
        return [
            {
                "claim_id": str(claim.id),
                "statement": claim.statement,
                "predicate": list(claim.predicate),
                "status": claim.status.value,
                "confidence": claim.confidence,
                "trust": round(trust.get("trust", 0.0), 6) if isinstance(trust, dict) else trust,
            }
            for claim, trust in results
        ]

    # -- research ---------------------------------------------------------------
    def research(
        self,
        question: str,
        *,
        claims: tuple[str, ...] = (),
        evidence: dict[str, tuple[float, str, float]] | None = None,
    ) -> dict[str, object]:
        """Run an evidence-aware research cycle and return the structured output."""
        from aura.research.engine import ResearchEngine
        from aura.research.models import ResearchInput, ResearchQuestion, SourceQuality

        quality: dict[str, object] = {"primary": SourceQuality.PRIMARY, "secondary": SourceQuality.SECONDARY,
                                      "tertiary": SourceQuality.TERTIARY, "unknown": SourceQuality.UNKNOWN}
        mapped_evidence: dict[str, tuple[float, object, float]] = {}
        for claim_text, (strength, source, freshness) in (evidence or {}).items():
            mapped_evidence[claim_text] = (strength, quality.get(source, SourceQuality.UNKNOWN), freshness)
        output = ResearchEngine().research(
            ResearchInput(
                question=ResearchQuestion.create(question),
                claims=claims,
                evidence=mapped_evidence,  # type: ignore[arg-type]
            )
        )
        return output.to_dict()

    # -- observability -----------------------------------------------------------
    def replay(self, execution_id: str) -> dict[str, Any]:
        from aura.observability.replay import ReplayEngine

        engine = ReplayEngine(self._brain.recorder)
        result = engine.trajectory(ExecutionId.from_str(execution_id))
        return {
            "execution_id": execution_id,
            "events": [e.to_dict() for e in result.trajectory()],
            "states": [
                {"sequence": s.at_sequence, "origin": s.origin, "state": s.state}
                for s in result.states
            ],
        }

    def provenance(self, execution_id: str) -> dict[str, Any]:
        return self._brain.provenance(ExecutionId.from_str(execution_id))

    def metrics(self) -> dict[str, Any]:
        return self._brain.metrics.snapshot()

    def health(self) -> dict[str, Any]:
        return self._brain.health()


__all__ = ["Aura"]