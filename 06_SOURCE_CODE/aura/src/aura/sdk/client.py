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
from aura.foundation.cancellation import CancellationToken
from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import CorrelationId, ExecutionId
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
        recorder: Any = None,
    ) -> None:
        self._config = config or AuraConfig()
        self._clock = clock or SystemClock()
        self._brain = BrainEngine.create(config=self._config, clock=self._clock, seed=seed, recorder=recorder)
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
        history: tuple[dict[str, str], ...] = (),
        scope: str | None = None,
        provider_authorized: bool = True,
        cancellation: CancellationToken | None = None,
    ) -> dict[str, Any]:
        """Run the full cognitive cycle and return a structured answer.

        ``provider_authorized`` is the API layer's 1C decision, carried through
        unchanged so the provider boundary can never be reached by an
        unauthorized request. It defaults to True for trusted local/SDK callers.
        ``cancellation`` is the caller's token: it propagates through the brain
        into reasoning and the provider transport so an in-flight call can be
        genuinely interrupted.
        """
        result = self._brain.reason(
            question=question,
            facts=facts,
            rules=rules,
            hypotheses=hypotheses,
            cases=cases,
            goal=goal,
            tasks=tasks,
            history=history,
            scope=scope,
            provider_authorized=provider_authorized,
            cancellation=cancellation,
        )
        return result.summary()

    def plan(
        self, *, goal: Goal, tasks: list[Task]
    ) -> dict[str, Any]:
        """Create a validated plan through the canonical planning engine.

        Delegates to the brain's planning engine so every plan is
        flight-recorded and traceable (the SDK never instantiates a second
        planner). Rejected plans (validation issues, dependency cycles) are
        recorded as ``plan.rejected`` events instead of raising.
        """
        result = self._brain.planning.plan(goal=goal, tasks=list(tasks))
        correlation = CorrelationId.new()
        execution = ExecutionId.new()
        if result.primary is None:
            self._brain.recorder.record(
                event_type="plan.rejected",
                source="aura.sdk.plan",
                execution_id=execution,
                correlation_id=correlation,
                payload={"goal": goal.description, "issues": list(result.issues)},
            )
            return {"plan_created": False, "issues": list(result.issues), "steps": []}
        self._brain.recorder.record(
            event_type="plan.created",
            source="aura.sdk.plan",
            execution_id=execution,
            correlation_id=correlation,
            payload={"plan_id": str(result.primary.id), "steps": result.primary.names},
        )
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
        scope: str | None = None,
    ) -> str:
        entry = self._brain.memory.remember(
            key=key, kind=kind, content=content, importance=importance, scope=scope
        )
        return str(entry.id)

    def recall(self, text: str, *, limit: int = 5, scope: str | None = None) -> list[dict[str, Any]]:
        entries = self._brain.memory.recall(MemoryQuery(text=text, limit=limit, scope=scope))
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
        scope: str = "owner:anonymous",
    ) -> dict[str, object]:
        """Run an evidence-aware research cycle and return the structured output.

        ``scope`` records the owning identity on the ``research.completed``
        flight-recorder event so run listings can be owner-isolated server
        side. It is carried only inside the event payload, never in the
        research output.
        """
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
        self._brain.recorder.record(
            event_type="research.completed",
            source="aura.sdk.research",
            execution_id=output.execution_id,
            correlation_id=CorrelationId.new(),
            payload={
                "question": question,
                "findings": len(output.findings),
                "epistemic": output.epistemic.value,
                "scope": scope,
            },
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