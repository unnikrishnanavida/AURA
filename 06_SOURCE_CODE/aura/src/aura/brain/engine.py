"""Brain: cognitive orchestration engine.

Wires memory, knowledge, reasoning, planning, reflection, learning, flight
recording, and observability behind one lifecycle, propagating confidence,
uncertainty, and provenance through every stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.config.settings import AuraConfig
from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import CorrelationId, ExecutionId
from aura.knowledge.engine import KnowledgeBase
from aura.learning.engine import LearningEngine
from aura.learning.models import LearningSignal
from aura.memory.engine import MemoryEngine, MemoryQuery
from aura.observability.flight_recorder import FlightRecorder, InMemoryFlightRecorder
from aura.observability.metrics import Metrics
from aura.observability.provenance import ProvenanceGraph
from aura.planning.engine import PlanningEngine
from aura.planning.models import Goal, Task
from aura.reasoning.engine import ReasoningEngine, ReasoningInput, ReasoningResult
from aura.reasoning.models import Case, Rule
from aura.reflection.engine import ReflectionEngine
from aura.reflection.models import Outcome, ReflectionSignal, SignalKind


@dataclass(frozen=True)
class StepSummary:
    stage: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"stage": self.stage, "detail": self.detail}


@dataclass
class BrainResult:
    execution_id: ExecutionId
    correlation_id: CorrelationId
    reasoning: ReasoningResult | None
    plan_created: bool = False
    plan_id: str | None = None
    plan_steps: list[str] = field(default_factory=list)
    reflections: list[ReflectionSignal] = field(default_factory=list)
    learning_signal: LearningSignal | None = None
    steps: list[StepSummary] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "correlation_id": str(self.correlation_id),
            "answer": self.reasoning.answer if self.reasoning else None,
            "confidence": self.reasoning.confidence if self.reasoning else None,
            "uncertainty": self.reasoning.uncertainty.value if self.reasoning else None,
            "plan_created": self.plan_created,
            "plan_steps": self.plan_steps,
            "reflections": [s.to_dict() for s in self.reflections],
            "steps": [s.to_dict() for s in self.steps],
        }


class BrainEngine:
    def __init__(
        self,
        *,
        memory: MemoryEngine,
        knowledge: KnowledgeBase,
        reasoning: ReasoningEngine,
        planning: PlanningEngine,
        reflection: ReflectionEngine,
        learning: LearningEngine,
        recorder: FlightRecorder,
        metrics: Metrics,
        clock: Clock,
        config: AuraConfig,
        logger: Any,
    ) -> None:
        self.memory = memory
        self.knowledge = knowledge
        self.reasoning = reasoning
        self.planning = planning
        self.reflection = reflection
        self.learning = learning
        self.recorder = recorder
        self.metrics = metrics
        self.clock = clock
        self.config = config
        self.logger = logger

    @classmethod
    def create(
        cls,
        *,
        config: AuraConfig | None = None,
        clock: Clock | None = None,
        seed: int | None = None,
    ) -> BrainEngine:
        from aura.observability.logging import get_logger

        cfg = config or AuraConfig()
        clk = clock or SystemClock()
        return cls(
            memory=MemoryEngine(),
            knowledge=KnowledgeBase(),
            reasoning=ReasoningEngine(seed=seed if seed is not None else cfg.engines.reasoning_seed),
            planning=PlanningEngine(),
            reflection=ReflectionEngine(),
            learning=LearningEngine(),
            recorder=InMemoryFlightRecorder(clock=clk),
            metrics=Metrics(),
            clock=clk,
            config=cfg,
            logger=get_logger("aura.brain"),
        )

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "engines": {
                "memory": self.memory.health(),
                "knowledge": self.knowledge.health(),
                "learning": self.learning.health(),
            },
            "recorded_events": self.recorder.count(),
        }

    def reason(
        self,
        *,
        question: str,
        facts: dict[str, float] | None = None,
        rules: tuple[Rule, ...] = (),
        hypotheses: tuple[str, ...] = (),
        prior: float = 0.5,
        cases: tuple[Case, ...] = (),
        likelihoods: dict[str, tuple[float, float]] | None = None,
        goal: Goal | None = None,
        tasks: list[Task] | None = None,
    ) -> BrainResult:
        correlation = CorrelationId.new()
        execution = ExecutionId.new()
        self.recorder.record(
            event_type="observation.recorded",
            source="brain.observe",
            execution_id=execution,
            correlation_id=correlation,
            payload={"question": question},
        )
        remembered = self.memory.recall(MemoryQuery(text=question))
        self.recorder.record(
            event_type="context.retrieved",
            source="brain.context",
            execution_id=execution,
            correlation_id=correlation,
            payload={"memories": len(remembered)},
        )
        reasoning_input = ReasoningInput(
            question=question,
            facts=dict(facts or {}),
            rules=rules,
            hypotheses=hypotheses,
            likelihoods=likelihoods or {},
            prior=prior,
            cases=cases,
            counterfactual_variable="",
        )
        reasoning_result = self.reasoning.reason(reasoning_input)
        self.recorder.record(
            event_type="decision",
            source="brain.interpret",
            execution_id=execution,
            correlation_id=correlation,
            payload={
                "answer": reasoning_result.answer,
                "confidence": reasoning_result.confidence,
                "uncertainty": reasoning_result.uncertainty.value,
            },
        )
        result = BrainResult(execution_id=execution, correlation_id=correlation, reasoning=reasoning_result)
        result.steps.append(StepSummary("observation", question))

        if goal is not None:
            plan_result = self.planning.plan(goal=goal, tasks=tasks or [])
            if plan_result.primary is not None:
                result.plan_created = True
                result.plan_id = str(plan_result.primary.id)
                result.plan_steps = plan_result.primary.names
                self.recorder.record(
                    event_type="plan.created",
                    source="brain.plan",
                    execution_id=execution,
                    correlation_id=correlation,
                    payload={"plan_id": result.plan_id, "steps": result.plan_steps},
                )
            result.steps.append(StepSummary("planning", "; ".join(result.plan_steps)))

        self._record_provenance(result)
        return result

    def reflect_and_learn(
        self,
        *,
        goal: str,
        success: bool,
        observed: dict[str, Any] | None = None,
        expected: dict[str, Any] | None = None,
        deviations: list[str] | None = None,
        events_summary: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> BrainResult:
        correlation = CorrelationId.new()
        execution = ExecutionId.new()
        outcome = Outcome(
            goal=goal,
            success=success,
            observed=observed or {},
            expected=expected or {},
            deviations=deviations or [],
            events_summary=events_summary or [],
            metrics=metrics or {},
        )
        report = self.reflection.reflect(outcome)
        self.recorder.record(
            event_type="reflection.completed",
            source="brain.reflect",
            execution_id=execution,
            correlation_id=correlation,
            payload={"signals": len(report.signals)},
        )
        result = BrainResult(execution_id=execution, correlation_id=correlation, reasoning=None)
        result.reflections = report.signals

        candidates = [
            s for s in report.signals if s.kind is SignalKind.IMPROVEMENT_SUGGESTION
        ]
        if candidates:
            signal = LearningSignal.create(
                kind="strategy_improvement",
                content=candidates[0].content,
                evidence=[{"score": 0.85}],
            )
            learning_result = self.learning.submit(signal)
            result.learning_signal = learning_result.signal
            self.recorder.record(
                event_type="learning.signal",
                source="brain.learn",
                execution_id=execution,
                correlation_id=correlation,
                payload=learning_result.outcome.to_dict(),
            )
        self._record_provenance(result)
        return result

    def provenance(self, execution_id: ExecutionId) -> dict[str, object]:
        graph = ProvenanceGraph()
        events = self.recorder.events(execution_id=execution_id)
        graph.load(events)
        if not events:
            return {"execution_id": str(execution_id), "cause_chain": []}
        return {"execution_id": str(execution_id), **graph.explain(str(events[-1].event_id))}

    def record_execution_memory(self, execution_id: ExecutionId) -> int:
        """Replay a recorded execution into episodic memory (post-hoc recall)."""
        from aura.memory.replay import ReplayToMemory

        entries = ReplayToMemory(self.memory.store, clock=self.clock).ingest_execution(
            self.recorder, execution_id
        )
        return len(entries)

    def _record_provenance(self, result: BrainResult) -> None:
        events = self.recorder.events(execution_id=result.execution_id)
        for i, event in enumerate(events):
            if i > 0:
                event.payload.setdefault("caused_by", [str(events[i - 1].event_id)])


Brain = BrainEngine

__all__ = ["Brain", "BrainEngine", "BrainResult", "StepSummary"]
