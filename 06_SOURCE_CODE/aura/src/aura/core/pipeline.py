"""Canonical request-flow pipeline.

The integrated, observable path every user request travels in AURA:

  REQUEST -> MEMORY -context-> KNOWLEDGE -context-> RESEARCH -claims->
  REASONING -> PLANNING -> SECURITY (guardrails/authorization) -> EXECUTION
  -> OBSERVATION -> VERIFICATION -> REFLECTION -> LEARNING SIGNAL ->
  MEMORY/KNOWLEDGE UPDATE -> AUDIT/TRACE/REPLAY.

Every boundary uses an existing canonical engine; this module only composes
them. Nothing is executed without passing the guardrail gate, applied changes
are learning-governed (validated, versioned, rollback-able), and every stage is
recorded in the flight recorder so the run can be replayed and audited.

The pipeline is deterministic: with the same inputs, clock, and registrations,
the same request produces the same decisions.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from aura.brain.engine import BrainEngine
from aura.execution.engine import ExecutionEngine, ExecutionRequest, ExecutionResult
from aura.execution.models import ActionInputs, WorldState
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.foundation.ids import CorrelationId, ExecutionId
from aura.learning.engine import LearningResult
from aura.learning.loop import LearningLoop
from aura.memory.engine import MemoryQuery
from aura.memory.models import MemoryType, Provenance
from aura.memory.policy import MemoryLifecycle
from aura.planning.engine import PlanningEngine, PlanResult
from aura.planning.models import Goal, Task
from aura.reflection.engine import ReflectionReport
from aura.reflection.models import Outcome, SignalKind
from aura.research.engine import ResearchEngine, ResearchOutput
from aura.research.models import EpistemicStatus, ResearchInput, ResearchQuestion, SourceQuality
from aura.security.audit import AuditLog
from aura.security.capabilities import Capability, CapabilityRegistry
from aura.security.guardrails import GuardrailService
from aura.security.permissions import Decision, Identity, PolicyEngine, Rule


@dataclass
class PipelineRequest:
    """One end-to-end request through the canonical flow."""

    question: str
    claims: tuple[str, ...] = ()
    knowledge_predicate: tuple[str, ...] = ()
    facts: dict[str, float] = field(default_factory=dict)
    goal: Goal | None = None
    tasks: tuple[Task, ...] = ()
    action_inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    identity: Identity | None = None
    approval: bool = False
    resource: str = "*"
    world: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageRecord:
    stage: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"stage": self.stage, "ok": self.ok, "detail": self.detail}


@dataclass
class PipelineResult:
    execution_id: ExecutionId
    correlation_id: CorrelationId
    reasoning: dict[str, object]
    research: ResearchOutput | None
    plan: PlanResult | None
    executions: list[ExecutionResult]
    security_decisions: list[dict[str, object]]
    reflection: ReflectionReport | None
    learning: LearningResult | None
    memory_ids: dict[str, str]
    success: bool
    steps: list[StageRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "correlation_id": str(self.correlation_id),
            "success": self.success,
            "reasoning": self.reasoning,
            "research": self.research.to_dict() if self.research else None,
            "plan": {
                "plan_id": str(self.plan.primary.id),
                "steps": self.plan.primary.names,
                "risk": self.plan.primary.risk.level if self.plan and self.plan.primary else None,
            }
            if self.plan and self.plan.primary
            else None,
            "executions": [e.to_dict() for e in self.executions],
            "security_decisions": self.security_decisions,
            "reflection": self.reflection.to_dict() if self.reflection else None,
            "learning": self.learning.to_dict() if self.learning else None,
            "memory_ids": self.memory_ids,
            "steps": [s.to_dict() for s in self.steps],
        }
def default_guardrails(registry: ActionRegistry) -> GuardrailService:
    """Build a guardrail service whose grants match the registered actions.

    Each action's capability is registered and allowed by policy. Risk above the
    autonomous ceiling (0.5) still requires approval, so high-risk actions are
    never auto-approved. Callers that need stricter policy should construct
    their own :class:`GuardrailService` and pass it to the pipeline.
    """
    capabilities = CapabilityRegistry()
    policies = PolicyEngine()
    for name in registry.names():
        spec = registry.get(name)
        capabilities.register(Capability(name=spec.capability))
        policies.add_rule(
            Rule(
                action=spec.capability,
                effect=Decision.ALLOW,
                name=f"allow-{name}",
                risk_max=0.5,
            )
        )
    return GuardrailService(capabilities=capabilities, policies=policies)


class ExecutionPipeline:
    """Composes memory, knowledge, research, reasoning, planning, security,
    execution, reflection, learning, and memory update behind one call."""

    def __init__(
        self,
        *,
        brain: BrainEngine | None = None,
        research: ResearchEngine | None = None,
        planning: PlanningEngine | None = None,
        registry: ActionRegistry | None = None,
        guardrails: GuardrailService | None = None,
        execution: ExecutionEngine | None = None,
        memory_lifecycle: MemoryLifecycle | None = None,
        learning_loop: LearningLoop | None = None,
        audit: AuditLog | None = None,
        max_parallel: int = 4,
    ) -> None:
        if max_parallel < 1:
            raise ValueError("max_parallel must be >= 1 (1 disables parallel scheduling)")
        self.brain = brain or BrainEngine.create()
        self.research = research or ResearchEngine()
        self.planning = planning or PlanningEngine()
        self.registry = registry or ActionRegistry()
        self.guardrails = guardrails or default_guardrails(self.registry)
        if execution is None:
            execution = ExecutionEngine(registry=self.registry, guardrails=self.guardrails)
        self.execution = execution
        self.memory_lifecycle = memory_lifecycle or MemoryLifecycle(engine=self.brain.memory)
        self.learning_loop = learning_loop or LearningLoop()
        self.audit = audit or AuditLog()
        self.max_parallel = max_parallel

    # -- pipeline ------------------------------------------------------------
    def run(
        self,
        request: PipelineRequest,
        *,
        cancellation: CancellationToken | None = None,
    ) -> PipelineResult:
        correlation = CorrelationId.new()
        execution_id = ExecutionId.new()
        steps: list[StageRecord] = []
        security: list[dict[str, object]] = []
        executions: list[ExecutionResult] = []
        memory_ids: dict[str, str] = {}
        learning: LearningResult | None = None

        self._record("pipeline.started", execution_id, correlation, {"question": request.question})
        if cancellation is not None:
            cancellation.check()

        # 1. MEMORY context
        remembered = self.brain.memory.recall(MemoryQuery(text=request.question, limit=5))
        steps.append(StageRecord("memory", True, f"recalled {len(remembered)} memories"))
        self._record("pipeline.stage", execution_id, correlation, {"stage": "memory", "count": len(remembered)})

        # 2. KNOWLEDGE context
        knowledge = self.brain.knowledge.retrieve(
            predicate=request.knowledge_predicate, statement=request.question, limit=10
        )
        steps.append(StageRecord("knowledge", True, f"retrieved {len(knowledge)} claims"))
        facts: dict[str, float] = dict(request.facts)
        for claim, trust in knowledge:
            facts.setdefault(claim.statement, round(trust["trust"] if isinstance(trust, dict) else 0.5, 6))

        # 3. RESEARCH (claims assessed against evidence)
        research_output: ResearchOutput | None = None
        if request.claims:
            evidence: dict[str, tuple[float, SourceQuality, float]] = {}
            for claim_text in request.claims:
                for claim_, trust in knowledge:
                    if claim_.statement == claim_text:
                        trust_value = trust["trust"] if isinstance(trust, dict) else 0.5
                        evidence[claim_text] = (round(trust_value, 6), SourceQuality.SECONDARY, 0.7)
                        break
                evidence.setdefault(claim_text, (0.2, SourceQuality.UNKNOWN, 0.3))
            research_output = self.research.research(
                ResearchInput(
                    question=ResearchQuestion.create(request.question),
                    claims=request.claims,
                    evidence=evidence,
                    execution_id=execution_id,
                )
            )
            steps.append(
                StageRecord(
                    "research",
                    True,
                    f"{len(research_output.findings)} findings, {len(research_output.contradictions)} contradictions",
                )
            )
            for finding in research_output.findings:
                facts.setdefault(finding.claim, round(finding.confidence, 6))

        # 4. REASONING
        reasoning_result = self.brain.reason(
            question=request.question, facts=facts, cancellation=cancellation
        )
        steps.append(
            StageRecord(
                "reasoning",
                True,
                f"answer confidence {reasoning_result.reasoning.confidence if reasoning_result.reasoning else 0.0}",
            )
        )
        self._record("pipeline.stage", execution_id, correlation, {"stage": "reasoning"})

        # 5. PLANNING
        plan: PlanResult | None = None
        if request.goal is not None:
            plan = self.planning.plan(goal=request.goal, tasks=list(request.tasks))
            steps.append(
                StageRecord(
                    "planning",
                    plan.primary is not None,
                    f"{len(plan.primary.steps) if plan.primary else 0} steps, issues={len(plan.issues)}",
                )
            )
            self._record("pipeline.stage", execution_id, correlation, {"stage": "planning"})
# 6. SECURITY + EXECUTION for every planned step (dependency-aware,
        # bounded-parallel scheduling of independent tasks; deterministic order).
        plan_steps = plan.primary.steps if plan and plan.primary else []
        self._dispatch_tasks(
            plan_steps,
            request,
            execution_id,
            correlation,
            steps,
            security,
            executions,
            cancellation,
        )

        # 7. OBSERVATION + VERIFICATION
        requires_execution = bool(plan_steps)
        observed: dict[str, object] = {
            result.request.action: result.action_result.output for result in executions
        }
        deviations = tuple(
            result.action_result.error or f"action {result.request.action} failed"
            for result in executions
            if not result.ok
        )
        all_executed_ok = (
            all(result.ok for result in executions) if executions else (not requires_execution)
        )
        success = all_executed_ok and bool(plan_steps if requires_execution else True)
        steps.append(
            StageRecord(
                "verification",
                success,
                f"{len(executions)} actions, {len(deviations)} failure(s)",
            )
        )
        self._record("pipeline.stage", execution_id, correlation, {"stage": "verification", "success": success})

        # 8. REFLECTION
        reflection: ReflectionReport | None = None
        if requires_execution:
            expected: dict[str, object] = {
                step.task.name: {"ok": True} for step in plan_steps if self.registry.has(step.task.name)
            }
            reflection = self.brain.reflection.reflect(
                Outcome(
                    goal=request.goal.description if request.goal else request.question,
                    success=success,
                    observed=observed,
                    expected=expected,
                    deviations=list(deviations),
                )
            )
            steps.append(StageRecord("reflection", True, f"{len(reflection.signals)} signal(s)"))
            self._record("pipeline.stage", execution_id, correlation, {"stage": "reflection"})

            # 9. LEARNING SIGNAL (governed; never mutates without validation)
            improvements = [
                s for s in reflection.signals if s.kind is SignalKind.IMPROVEMENT_SUGGESTION
            ]
            if improvements:
                self.learning_loop.observe(
                    event_type="pipeline.execution",
                    expected={"success": 1.0},
                    observed={"success": 1.0 if success else 0.0},
                    deviations=deviations,
                )
                learning = self.learning_loop.evaluate_and_learn(event_type="pipeline.execution")
                steps.append(StageRecord("learning", learning is not None, "loop evaluated outcome"))
                self._record(
                    "pipeline.stage",
                    execution_id,
                    correlation,
                    {"stage": "learning", "signals": len(improvements)},
                )

        # 10. MEMORY / KNOWLEDGE UPDATE
        episodic = self.brain.memory.remember(
            key=f"pipeline:{request.question[:40]}",
            kind=MemoryType.EPISODIC,
            content={
                "question": request.question,
                "success": success,
                "executions": [r.request.action for r in executions],
                "deviations": list(deviations),
            },
            importance=0.5 if success else 0.8,
            provenance=Provenance(source="execution.pipeline", execution_id=execution_id),
        )
        memory_ids["episodic"] = str(episodic.id)
        steps.append(StageRecord("memory_update", True, f"recorded {str(episodic.id)}"))

        verified = (
            [
                finding
                for finding in (research_output.findings if research_output else [])
                if finding.status is EpistemicStatus.EVIDENCE and finding.confidence >= 0.7
            ]
            if research_output
            else []
        )
        for finding in verified:
            from aura.knowledge.models import Claim

            claim = Claim.create(
                statement=finding.claim,
                predicate=request.knowledge_predicate or (finding.status.value,),
            )
            self.brain.knowledge.add(claim)
            memory_ids.setdefault("knowledge", str(claim.id))
        if verified:
            steps.append(StageRecord("knowledge_update", True, f"ingested {len(verified)} verified claim(s)"))

        self._record("pipeline.completed", execution_id, correlation, {"success": success})
        return PipelineResult(
            execution_id=execution_id,
            correlation_id=correlation,
            reasoning=reasoning_result.summary(),
            research=research_output,
            plan=plan,
            executions=executions,
            security_decisions=security,
            reflection=reflection,
            learning=learning,
            memory_ids=memory_ids,
            success=success,
            steps=steps,
        )

    # -- scheduling ---------------------------------------------------------
    def _dispatch_tasks(
        self,
        plan_steps: Any,
        request: PipelineRequest,
        execution_id: ExecutionId,
        correlation: CorrelationId,
        steps: list[StageRecord],
        security: list[dict[str, object]],
        executions: list[ExecutionResult],
        cancellation: CancellationToken | None,
    ) -> None:
        """Execute planned steps in dependency waves (ORCH-1).

        Each wave contains only tasks whose prerequisites are all satisfied —
        independent by construction — so it is safe to run them concurrently on
        a bounded thread pool (``max_parallel``). Results are collected back in
        plan order, so pipeline results stay deterministic. Cancellation is
        checked before every wave; a cancelled request never schedules new work
        and marks remaining tasks as cancelled.
        """
        if not plan_steps:
            return
        pending: dict[str, Any] = {step.task.name: step for step in plan_steps}
        completed: set[str] = set()
        while pending:
            if cancellation is not None and cancellation.cancelled:
                for name in list(pending):
                    steps.append(
                        StageRecord("execution", False, f"{name}: cancelled before execution")
                    )
                return
            ready = [
                name for name, step in pending.items() if step.prerequisites_met(completed)
            ]
            if not ready:
                # Cycle guard (defensive: the plan validator rejects cycles
                # upstream, so this branch is unreachable in normal operation).
                for name in list(pending):
                    steps.append(
                        StageRecord(
                            "execution", False, f"{name}: unresolved dependency; not executed"
                        )
                    )
                    del pending[name]
                return
            with ThreadPoolExecutor(max_workers=min(self.max_parallel, len(ready))) as pool:
                futures = {
                    name: pool.submit(
                        self._execute_one_task,
                        pending[name],
                        request,
                        execution_id,
                        correlation,
                        cancellation,
                    )
                    for name in ready
                }
                for name in ready:
                    local_steps, local_security, local_executions = futures[name].result()
                    steps.extend(local_steps)
                    security.extend(local_security)
                    executions.extend(local_executions)
            completed.update(ready)
            for name in ready:
                del pending[name]

    def _execute_one_task(
        self,
        step: Any,
        request: PipelineRequest,
        execution_id: ExecutionId,
        correlation: CorrelationId,
        cancellation: CancellationToken | None,
    ) -> tuple[list[StageRecord], list[dict[str, object]], list[ExecutionResult]]:
        """Run the full gate -> audit -> execute sequence for one planned task.

        Runs on a worker thread when tasks are dispatched in parallel. All
        shared state it touches is thread-guarded (budget tracker, flight
        recorder, execution idempotency set). It returns *local* record lists
        that the dispatcher merges in deterministic plan order, so concurrent
        completion order never leaks into results.
        """
        task = step.task
        local_steps: list[StageRecord] = []
        local_security: list[dict[str, object]] = []
        local_executions: list[ExecutionResult] = []
        gate = self.guardrails.check(
            action=task.capability,
            resource=request.resource,
            identity=request.identity,
            risk=task.risk,
            approval=request.approval,
            cost=task.estimated_cost,
            tokens=0,
        )
        local_security.append({"task": task.name, "allowed": gate.allowed, "reason": gate.reason})
        self.audit.record(
            action=task.capability,
            actor=request.identity.id if request.identity else "anonymous",
            resource=request.resource,
            decision="allow" if gate.allowed else "deny",
            reason=gate.reason,
            correlation_id=str(correlation),
        )
        if not gate.allowed:
            local_steps.append(StageRecord("security", False, f"{task.name}: {gate.reason}"))
            return local_steps, local_security, local_executions
        if not self.registry.has(task.name):
            local_steps.append(
                StageRecord("execution", False, f"action {task.name!r} not registered")
            )
            return local_steps, local_security, local_executions
        local_steps.append(StageRecord("security", True, f"{task.name}: {gate.reason}"))

        inputs = ActionInputs(values=dict(request.action_inputs.get(task.name, {})))
        world = WorldState(values=dict(request.world))
        result = self.execution.execute(
            ExecutionRequest(
                action=task.name,
                inputs=inputs,
                world_state=world,
                execution_id=execution_id,
                approval=request.approval,
            ),
            cancellation=cancellation,
        )
        local_executions.append(result)
        self._record(
            "pipeline.action",
            execution_id,
            correlation,
            {"action": task.name, "ok": result.ok, "attempts": result.attempts},
        )
        local_steps.append(
            StageRecord(
                "execution",
                result.ok,
                f"{task.name}: ok={result.ok} attempts={result.attempts} replayed={result.replayed}",
            )
        )
        return local_steps, local_security, local_executions

    # -- helpers -------------------------------------------------------------
    def _record(
        self, event_type: str, execution_id: ExecutionId, correlation: CorrelationId, payload: dict[str, object]
    ) -> None:
        self.brain.recorder.record(
            event_type=event_type,
            source="aura.core.pipeline",
            execution_id=execution_id,
            correlation_id=correlation,
            payload=payload,
        )


__all__ = [
    "ExecutionPipeline",
    "PipelineRequest",
    "PipelineResult",
    "StageRecord",
    "default_guardrails",
]