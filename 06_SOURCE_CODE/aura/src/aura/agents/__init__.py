"""AURA agents bridge.

Integrates the optional guarded agent runtime (``aura-agents``) behind the
platform. The bridge is intentionally the only entry point: delegated agents
inherit the platform's security boundaries (capabilities, permissions,
safety, budgets) and never bypass them.

Phase 1F: activation seam. ``build_agent`` composes the existing agent runtime
through its own public DSL (no new agent system), optionally wiring canonical
AURA memory through the agent package's sanctioned ``CanonicalMemoryProvider``;
``run_agent_task`` / ``run_agent_action`` execute through the agent's guarded
cognitive loop / execution pipeline and honour the canonical cancellation
token. Tools, allow-rules and capabilities are only ever supplied by trusted
caller code -- never from the network boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.errors import CancelledError
from aura.input.multimodal import MultimodalObservation

_AGENTS_INSTALLED = False
try:
    import aura_agent  # noqa: F401

    _AGENTS_INSTALLED = True
except ImportError:  # pragma: no cover - optional dependency
    _AGENTS_INSTALLED = False


def agents_available() -> bool:
    """Return True when the optional AURA agents runtime is installed."""
    return _AGENTS_INSTALLED


class AgentsBridgeError(RuntimeError):
    """Raised when the agents runtime is required but not installed."""


def require_agents() -> Any:
    """Import the agents runtime or raise a helpful error."""
    if not _AGENTS_INSTALLED:
        raise AgentsBridgeError(
            "the AURA agents runtime is not installed; install with 'pip install aura[agents]'"
        )
    import aura_agent

    return aura_agent


@dataclass
class AgentTaskResult:
    """Canonical outcome envelope of one agent goal through the bridge."""

    agent_id: str
    goal_id: str | None = None
    success: bool = False
    reason: str = ""
    iterations: int = 0
    final_message: str = ""
    cancelled: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)
    #: Phase 1H: the canonical research stage outcome when research ran
    #: (empty when research was not part of this task).
    research: dict[str, Any] | None = None
    #: Phase 1I: verification + reflection + learning-candidate outcome.
    evaluation: dict[str, Any] | None = None
    #: Phase 1J: accepted multimodal observations (serialized, verified=False).
    observations: tuple[dict[str, Any], ...] = ()


@dataclass
class AgentActionResult:
    """Canonical outcome envelope of one guarded agent action."""

    agent_id: str
    tool_name: str
    execution_id: str | None = None
    success: bool = False
    state: str | None = None
    error: str | None = None
    failure_class: str | None = None
    cancelled: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)


def build_agent(
    *,
    name: str = "aura-agent",
    capabilities: tuple[str, ...] = (),
    allow_rules: tuple[tuple[str, str], ...] = (),
    tools: tuple[Any, ...] = (),
    memory: Any = None,
    canonical: CanonicalContext | None = None,
) -> Any:
    """Compose a guarded :class:`AgentRuntime` via the existing agent DSL.

    ``tools`` are :class:`~aura_agent.tools.models.Tool` objects supplied by
    trusted caller code; ``allow_rules`` are ``(action, resource)`` pairs; the
    policy is base-deny by construction. When ``memory`` is a canonical
    ``aura.memory.engine.MemoryEngine``, the agent's memory bridge is wired to
    it through the agent package's ``CanonicalMemoryProvider``.

    Phase 1G: ``canonical`` (:class:`CanonicalContext`) wires the agent's
    bridges to canonical engines -- reasoning through the canonical
    BrainEngine (ContextAssembler -> memory + knowledge -> ReasoningEngine),
    planning through the canonical PlanningEngine, and execution through
    guarded canonical actions registered as agent tools. Every seam is reuse,
    never a copy.
    """
    agent_mod = require_agents()
    import aura_agent.api  # noqa: F401  (public surface: AgentBuilder)

    builder = agent_mod.api.AgentBuilder(name=name)
    for tool in tools or ():
        builder.with_tool(tool)
    for action, resource in allow_rules or ():
        builder.allow(action=action, resource=resource)
    for capability in capabilities or ():
        builder.with_capability(capability)
    if canonical is not None and canonical.action_registry is not None and canonical.execution is not None:
        for action_name in canonical.action_registry.names():
            builder.with_tool(
                canonical_action_tool(
                    action_registry=canonical.action_registry,
                    action_name=action_name,
                    execution=canonical.execution,
                )
            )
        for action, resource in canonical.allow_rules or ():
            builder.allow(action=action, resource=resource)
    agent = builder.build()
    memory_engine = memory if memory is not None else (canonical.memory if canonical is not None else None)
    if memory_engine is not None:
        from aura_agent.memory_bridge.canonical_adapter import CanonicalMemoryProvider

        agent.components.memory_bridge = agent_mod.memory_bridge.MemoryBridge(
            provider=CanonicalMemoryProvider(memory_engine)
        )
    if canonical is not None:
        if canonical.brain is not None:
            agent.components.reasoning_bridge = agent_mod.reasoning_bridge.ReasoningBridge(
                provider=CanonicalReasoningProvider(canonical.brain)
            )
        if canonical.planning is not None:
            action_names = (
                tuple(canonical.action_registry.names())
                if canonical.action_registry is not None
                else ()
            )
            agent.components.planning_bridge = agent_mod.planning_bridge.PlanningBridge(
                provider=CanonicalPlanningProvider(canonical.planning, action_names)
            )
    return agent


def build_task_agent(*, memory: Any = None) -> Any:
    """Build the default safe agent (no tools, no capabilities) with optional
    canonical memory wiring. Exists for symmetry and safe default use."""
    return build_agent(memory=memory)


def _event_dicts(recorder: Any) -> list[dict[str, Any]]:
    """Serialize flight-recorder events into JSON-safe dicts."""
    events_fn = getattr(recorder, "events", None)
    if events_fn is None:
        return []
    out: list[dict[str, Any]] = []
    for event in events_fn():
        payload: dict[str, Any] = {
            "event_type": event.event_type,
            "payload": event.payload,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
        }
        if event.execution_id is not None:
            payload["execution_id"] = str(event.execution_id)
        if event.agent_id is not None:
            payload["agent_id"] = str(event.agent_id)
        if event.goal_id is not None:
            payload["goal_id"] = str(event.goal_id)
        out.append(payload)
    return out
@dataclass
class ResearchStageResult:
    """Canonical outcome of one research-stage through the task lifecycle."""

    state: str
    execution_id: str
    state_history: tuple[str, ...] = ()
    question: str = ""
    findings: list[dict[str, Any]] = field(default_factory=list)
    synthesis: str = ""
    overall_confidence: float = 0.0
    epistemic: str = ""
    contradictions: list[list[str]] = field(default_factory=list)
    #: claim -> confidence for findings that passed the engine's verification
    #: rules (EVIDENCE/INFERENCE). What feeds reasoning.
    research_facts: dict[str, float] = field(default_factory=dict)
    cancelled: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "execution_id": self.execution_id,
            "state_history": list(self.state_history),
            "question": self.question,
            "findings": self.findings,
            "synthesis": self.synthesis,
            "overall_confidence": self.overall_confidence,
            "epistemic": self.epistemic,
            "contradictions": self.contradictions,
            "verified_facts": self.research_facts,
            "cancelled": self.cancelled,
            "error": self.error,
        }


def run_research_stage(
    *,
    research: Any,
    question: str,
    claims: tuple[str, ...] = (),
    evidence: dict[str, tuple[float, str, float]] | None = None,
    cancellation: Any = None,
    record: Any = None,
) -> ResearchStageResult:
    """Run the canonical ResearchEngine as one bounded lifecycle stage.

    The canonical engine is a deterministic, evidence-aware evaluator (it does
    not fetch external sources): RETRIEVED here means "supplied evidence was
    assessed", VERIFIED means "at least one finding cleared the engine's
    verification rules for EVIDENCE/INFERENCE" -- never assumed from retrieval
    alone. No evidence is ever fabricated; a failure or cancellation is
    reported truthfully and the stage never fabricates a success.
    """
    from aura.research.engine import ResearchEngine
    from aura.research.models import (
        EpistemicStatus,
        ResearchInput,
        ResearchQuestion,
        ResearchState,
        SourceQuality,
    )

    if not isinstance(research, ResearchEngine):
        return ResearchStageResult(
            state=ResearchState.FAILED.value,
            execution_id="",
            state_history=(ResearchState.REQUESTED.value, ResearchState.FAILED.value),
            error="research unavailable",
        )

    def _finish(state: str, **kw: Any) -> ResearchStageResult:
        return ResearchStageResult(
            state=state,
            execution_id=execution_id,
            state_history=tuple(history),
            question=question,
            **kw,
        )

    history: list[str] = [ResearchState.REQUESTED.value, ResearchState.PLANNED.value]
    execution_id = ""
    if cancellation is not None and cancellation.cancelled:
        history.append(ResearchState.CANCELLED.value)
        return _finish(ResearchState.CANCELLED.value, cancelled=True)

    # Normalize string source names to SourceQuality enums (the engine and its
    # to_dict expect enums; the SDK performs the same mapping).
    _quality = {
        "primary": SourceQuality.PRIMARY,
        "secondary": SourceQuality.SECONDARY,
        "tertiary": SourceQuality.TERTIARY,
    }
    evidence_map: dict[str, tuple[float, SourceQuality, float]] = {}
    for claim, (strength, source, freshness) in (evidence or {}).items():
        quality = source if isinstance(source, SourceQuality) else _quality.get(str(source), SourceQuality.UNKNOWN)
        evidence_map[str(claim)] = (float(strength), quality, float(freshness))

    try:
        inp = ResearchInput(
            question=ResearchQuestion.create(question),
            claims=tuple(str(c) for c in claims),
            evidence=evidence_map,
        )
        output = research.research(inp)
        execution_id = str(output.execution_id)
    except CancelledError:
        history.append(ResearchState.CANCELLED.value)
        return _finish(ResearchState.CANCELLED.value, cancelled=True)
    except Exception as exc:  # noqa: BLE001 - a research failure is a report, never a crash
        history.append(ResearchState.FAILED.value)
        return _finish(ResearchState.FAILED.value, error=f"{type(exc).__name__}: {exc}")

    history.append(ResearchState.RETRIEVED.value)
    if cancellation is not None and cancellation.cancelled:
        history.append(ResearchState.CANCELLED.value)
        return _finish(ResearchState.CANCELLED.value, cancelled=True)

    findings: list[dict[str, Any]] = []
    facts: dict[str, float] = {}
    for finding in output.findings:
        findings.append(finding.to_dict())
        if finding.status in (EpistemicStatus.EVIDENCE, EpistemicStatus.INFERENCE):
            facts[finding.claim] = float(finding.confidence)

    state = ResearchState.VERIFIED.value if facts else ResearchState.RETRIEVED.value
    history.append(state)
    result = _finish(
        state,
        findings=findings,
        synthesis=output.synthesis,
        overall_confidence=float(output.overall_confidence),
        epistemic=output.epistemic.value,
        contradictions=[list(pair) for pair in output.contradictions],
        research_facts=facts,
    )
    if record is not None:
        import contextlib

        with contextlib.suppress(Exception):  # provenance must not break research  # noqa: BLE001
            record(result.to_dict())
    return result


@dataclass
class TaskEvaluation:
    """Verification + reflection + learning-candidate outcome of one task.

    A learning candidate produced here is *never* active: it must pass the
    existing approval gate (:class:`~aura.learning.gate.SignalValidator`) via
    an explicit server-side decision before it is applied by the canonical
    versioned :class:`~aura.learning.registry.LearningRegistry`.
    """

    verification_status: str
    verification_reason: str = ""
    reflection_summary: str = ""
    signals: list[dict[str, Any]] = field(default_factory=list)
    learning_status: str = "none"  # none | candidate
    candidate_id: str | None = None
    candidate_kind: str | None = None
    candidate_content: str | None = None
    evidence_count: int = 0
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_status": self.verification_status,
            "verification_reason": self.verification_reason,
            "reflection_summary": self.reflection_summary,
            "signals": self.signals,
            "learning_status": self.learning_status,
            "candidate_id": self.candidate_id,
            "candidate_kind": self.candidate_kind,
            "candidate_content": self.candidate_content,
            "evidence_count": self.evidence_count,
            "provenance": self.provenance,
        }


def evaluate_task_outcome(
    *,
    goal: str,
    success: bool,
    cancelled: bool,
    observed: dict[str, Any] | None = None,
    expected: dict[str, Any] | None = None,
    deviations: tuple[str, ...] = (),
    events_summary: tuple[str, ...] = (),
    metrics: dict[str, float] | None = None,
    learning_confidence_threshold: float = 0.5,
) -> TaskEvaluation:
    """Verification -> reflection -> learning *candidate* for one task outcome.

    - Verification is derived from the REAL observed outcome (any cancelled
      task is ``cancelled``; a successful task with recorded execution events
      is ``verified``; otherwise ``failed`` / ``inconclusive``) -- never
      fabricated.
    - Reflection runs the canonical ReflectionEngine over the real outcome.
    - A learning *candidate* (status ``candidate``) is produced only when
      reflection surfaced a genuine lesson/improvement (e.g. a failure or a
      deviation) -- a clean success rarely asks to change anything.
    The candidate is NEVER auto-applied here.
    """
    from aura.learning.models import LearningSignal
    from aura.reflection.engine import ReflectionEngine
    from aura.reflection.models import Outcome, SignalKind

    if cancelled:
        return TaskEvaluation(
            verification_status="cancelled",
            verification_reason="task was cancelled; no outcome to verify or learn from",
            reflection_summary="",
            learning_status="none",
            provenance={"source": "agent.evaluation", "goal": goal, "success": False, "cancelled": True},
        )

    if success and events_summary:
        verification_status = "verified"
        verification_reason = "observed outcome met expectations with recorded execution events"
    elif success:
        verification_status = "inconclusive"
        verification_reason = "task succeeded but no execution events were observed; cannot confirm an effect"
    else:
        verification_status = "failed"
        verification_reason = "the observed outcome did not meet expectations"

    outcome = Outcome(
        goal=goal,
        success=bool(success),
        observed=dict(observed or {}),
        expected=dict(expected or {}),
        deviations=list(deviations),
        events_summary=list(events_summary),
        metrics=dict(metrics or {}),
    )
    report = ReflectionEngine().reflect(outcome)

    signals = [s.to_dict() for s in report.signals]
    candidate = None
    for signal in report.signals:
        if signal.kind in (SignalKind.LESSON, SignalKind.IMPROVEMENT_SUGGESTION) and signal.confidence >= learning_confidence_threshold:
            candidate = LearningSignal.create(
                kind="agent_reflection",
                content=signal.content,
                evidence=[{"score": round(signal.confidence, 6)}],
            )
            break

    if candidate is None:
        return TaskEvaluation(
            verification_status=verification_status,
            verification_reason=verification_reason,
            reflection_summary=report.summary,
            signals=signals,
            learning_status="none",
            provenance={"source": "agent.evaluation", "goal": goal, "success": bool(success)},
        )

    return TaskEvaluation(
        verification_status=verification_status,
        verification_reason=verification_reason,
        reflection_summary=report.summary,
        signals=signals,
        learning_status="candidate",
        candidate_id=candidate.id,
        candidate_kind=candidate.kind,
        candidate_content=candidate.content,
        evidence_count=len(candidate.evidence),
        provenance={"source": "agent.evaluation", "goal": goal, "success": bool(success), "candidate": candidate.id},
    )


def run_agent_task(
    *,
    agent: Any,
    description: str,
    success_criteria: tuple[str, ...] = (),
    capabilities: tuple[str, ...] = (),
    world_state: dict[str, Any] | None = None,
    cancellation: Any = None,
    research: Any = None,
    research_claims: tuple[str, ...] = (),
    research_evidence: dict[str, tuple[float, str, float]] | None = None,
    require_research: bool = False,
    observations: tuple[MultimodalObservation, ...] = (),
) -> AgentTaskResult:
    """Execute one goal through the agent's bounded cognitive loop.

    The canonical cancellation token is honoured before dispatch; a token that
    fires while the loop runs is reported truthfully (``cancelled=True``) once
    the bounded loop returns. The agent run is bounded by its own loop
    iteration cap and per-tool timeouts.

    Phase 1H: when ``research`` (a canonical ``ResearchEngine``) is supplied
    and research is requested (``research_claims`` or ``require_research``),
    a canonical research stage runs first and verified findings feed canonical
    reasoning as facts. When ``require_research`` is True, a cancelled, failed
    or unverified research stage abstains honestly (no execution runs) rather
    than fabricating evidence.
    """
    if cancellation is not None and cancellation.cancelled:
        raise CancelledError("agent task cancelled before start")

    research_block: dict[str, Any] | None = None
    research_ran = research is not None and (require_research or bool(research_claims))

    if research_ran:
        stage = run_research_stage(
            research=research,
            question=description,
            claims=research_claims,
            evidence=research_evidence,
            cancellation=cancellation,
        )
        research_block = stage.to_dict()
        try:  # reuse the agent's flight recorder for research provenance
            from aura_agent.flight_recorder.events.agent_event import AgentEvent

            agent.components.flight_recorder.record(
                AgentEvent(
                    event_type="research.completed",
                    payload={
                        "state": stage.state,
                        "question": description,
                        "execution_id": stage.execution_id,
                        "findings": len(stage.findings),
                        "verified_facts": dict(stage.research_facts),
                    },
                )
            )
        except Exception:  # noqa: BLE001 - provenance recording must not break the task
            pass
        if stage.research_facts:
            provider = getattr(
                getattr(agent.components, "reasoning_bridge", None), "provider", None
            )
            if provider is not None and hasattr(provider, "set_research_facts"):
                provider.set_research_facts(stage.research_facts)
        if require_research:
            if stage.state == "cancelled":
                return AgentTaskResult(
                    agent_id=str(agent.agent_id),
                    success=False,
                    reason=stage.error or "research cancelled",
                    cancelled=True,
                    events=_event_dicts(agent.components.flight_recorder),
                    research=research_block,
                )
            if stage.state == "failed":
                return AgentTaskResult(
                    agent_id=str(agent.agent_id),
                    success=False,
                    reason=f"research failed: {stage.error or 'research unavailable'}",
                    events=_event_dicts(agent.components.flight_recorder),
                    research=research_block,
                )
            if stage.state != "verified":
                return AgentTaskResult(
                    agent_id=str(agent.agent_id),
                    success=False,
                    reason="research did not verify the required evidence",
                    events=_event_dicts(agent.components.flight_recorder),
                    research=research_block,
                )

    goal = agent.create_goal(
        description=description, success_criteria=list(success_criteria)
    )
    if observations:
        reason_provider = getattr(
            getattr(agent.components, "reasoning_bridge", None), "provider", None
        )
        if reason_provider is not None and hasattr(reason_provider, "set_observations"):
            reason_provider.set_observations(tuple(observations))
    try:
        outcome = agent.run_goal(
            goal=goal,
            world_state=world_state or {},
            capabilities=list(capabilities),
        )
    except Exception as exc:  # noqa: BLE001 - a failed task is a report, never a crash
        return AgentTaskResult(
            agent_id=str(agent.agent_id),
            goal_id=str(goal.id) if goal.id is not None else None,
            success=False,
            reason=f"agent runtime failure: {type(exc).__name__}: {exc}",
            cancelled=cancellation is not None and cancellation.cancelled,
            events=_event_dicts(agent.components.flight_recorder),
            research=research_block,
            evaluation=None,
        )
    cancelled = cancellation is not None and cancellation.cancelled
    evaluation_block: dict[str, Any] | None = None
    if not cancelled:
        events = _event_dicts(agent.components.flight_recorder)
        events_summary = tuple(e.get("event_type", "") for e in events if e.get("event_type"))
        result_state = getattr(outcome, "result", None) or {}
        evaluation_block = evaluate_task_outcome(
            goal=description,
            success=bool(outcome.success),
            cancelled=False,
            observed={**{"success": bool(outcome.success)}, **dict(result_state)},
            expected={"success": True},
            deviations=() if outcome.success else (str(getattr(outcome, "reason", "goal failed")),),
            events_summary=events_summary,
            metrics={
                "expected_actions": 1.0,
                "actions_used": float(int(getattr(outcome, "iterations", 1)) or 1),
            },
        ).to_dict()
    return AgentTaskResult(
        agent_id=str(agent.agent_id),
        goal_id=str(goal.id) if goal.id is not None else None,
        success=bool(outcome.success) and not cancelled,
        reason=str(getattr(outcome, "reason", "")) if not cancelled else "cancelled by caller",
        iterations=int(getattr(outcome, "iterations", 0)),
        final_message=str(getattr(outcome, "final_message", "")),
        cancelled=cancelled,
        events=_event_dicts(agent.components.flight_recorder),
        research=research_block,
        evaluation=evaluation_block,
        observations=tuple(obs.to_dict() for obs in observations),
    )


def run_agent_action(
    *,
    agent: Any,
    tool_name: str,
    capability: str,
    inputs: dict[str, Any] | None = None,
    execution_id: str | None = None,
    cancellation: Any = None,
) -> AgentActionResult:
    """Run one guarded action through the agent's execution pipeline.

    Policy denials (capability / permission / safety / constitution /
    approval / budget) are returned as structured failures, never fabricated
    results. ``execution_id`` is optional and lets callers attach a budget to
    the exact execution before dispatch.
    """
    if cancellation is not None and cancellation.cancelled:
        raise CancelledError("agent action cancelled before dispatch")
    from aura_agent.contracts.errors import DomainError
    from aura_agent.contracts.ids import ActionId, ExecutionId
    from aura_agent.execution_bridge import ExecutionRequest

    request = ExecutionRequest(
        action_id=ActionId.new(),
        tool_name=tool_name,
        capability=capability,
        agent_id=agent.agent_id,
        inputs=dict(inputs or {}),
        execution_id=ExecutionId(execution_id) if execution_id is not None else None,
    )
    try:
        result = agent.execute_action(request)
    except DomainError as exc:
        return AgentActionResult(
            agent_id=str(agent.agent_id),
            tool_name=tool_name,
            success=False,
            state="denied",
            error=exc.message,
            failure_class=_denial_class(exc),
            cancelled=cancellation is not None and cancellation.cancelled,
            events=_event_dicts(agent.components.flight_recorder),
        )
    except Exception as exc:  # noqa: BLE001 - honest failure reporting at the boundary
        return AgentActionResult(
            agent_id=str(agent.agent_id),
            tool_name=tool_name,
            success=False,
            state="failed",
            error=f"{type(exc).__name__}: {exc}",
            cancelled=cancellation is not None and cancellation.cancelled,
            events=_event_dicts(agent.components.flight_recorder),
        )
    primary = result.primary
    failure_class = None
    if primary is not None and primary.failure_class is not None:
        failure_class = primary.failure_class.value
    return AgentActionResult(
        agent_id=str(agent.agent_id),
        tool_name=tool_name,
        execution_id=str(result.execution_id),
        success=bool(result.success),
        state=getattr(result, "state", None),
        error=primary.error if primary is not None else None,
        failure_class=failure_class,
        cancelled=cancellation is not None and cancellation.cancelled,
        events=_event_dicts(agent.components.flight_recorder),
    )


@dataclass
class CanonicalContext:
    """Canonical engine wiring handed to the agent bridge (reuse, never copies).

    All fields are canonical ``aura`` engine instances: ``brain``
    (``BrainEngine``), ``memory`` (``MemoryEngine``), ``planning``
    (``PlanningEngine``), ``action_registry`` (``ActionRegistry`` of the
    actions the operator exposes to this agent) and ``execution``
    (``ExecutionEngine`` that guards those actions). ``allow_rules`` grants
    the agent permission to the exposed action namespace.
    """

    brain: Any = None
    memory: Any = None
    planning: Any = None
    action_registry: Any = None
    execution: Any = None
    allow_rules: tuple[tuple[str, str], ...] = (("actions.*", "*"),)


class CanonicalReasoningProvider:
    """Agent reasoning through the canonical BrainEngine.

    Each loop consultation runs canonical reasoning end to end: context
    assembly (canonical memory + knowledge via ContextAssembler) followed by
    the canonical ReasoningEngine. A provider failure is reported explicitly
    (answer ``no_usable_plan`` + ``provider_error`` metadata), never simulated.
    """

    def __init__(self, brain: Any) -> None:
        self._brain = brain
        self._research_facts: dict[str, float] = {}
        self._observations: tuple[MultimodalObservation, ...] = ()

    def set_research_facts(self, facts: dict[str, float]) -> None:
        """Attach research-derived evidence so canonical reasoning sees it as
        additional grounded facts (the existing ``ReasoningInput.facts`` seam).
        Research evidence is merged in but always remains distinguishable from
        memory/knowledge by its origin in the research stage result."""
        self._research_facts = dict(facts or {})

    def set_observations(self, observations: tuple[MultimodalObservation, ...]) -> None:
        """Attach validated multimodal observations so canonical reasoning sees
        them as untrusted (``verified=False``) grounding context, mirroring how
        research facts are injected through the existing reasoning seam."""
        self._observations = tuple(observations)

    def reason(self, request: Any) -> Any:
        from aura_agent.reasoning_bridge import ReasoningResult

        try:
            brain_result = self._brain.reason(
                question=request.objective,
                facts=dict(self._research_facts),
                observations=self._observations,
            )
        except Exception as exc:  # noqa: BLE001 - report the failure honestly
            return ReasoningResult(
                answer="no_usable_plan",
                confidence=0.0,
                metadata={"provider_error": f"{type(exc).__name__}: {exc}"},
                provider="canonical.brain",
            )
        reasoning = getattr(brain_result, "reasoning", None)
        answer = brain_result.direct_answer
        if not answer and reasoning is not None:
            answer = getattr(reasoning, "answer", None) or "no_usable_plan"
        confidence = float(getattr(reasoning, "confidence", 0.0) or 0.0)
        return ReasoningResult(
            answer=str(answer or "no_usable_plan"),
            confidence=confidence,
            metadata={"execution_id": str(brain_result.execution_id)},
            provider="canonical.brain",
        )


class CanonicalPlanningProvider:
    """Agent planning through the canonical PlanningEngine.

    Candidate tasks are derived only from the action tools registered by the
    operator; the canonical engine validates, orders and risks them. Steps
    carry the agent's tool/capability contract so the guarded loop can execute
    them.
    """

    def __init__(self, planning: Any, action_names: tuple[str, ...]) -> None:
        self._planning = planning
        self._actions = tuple(action_names)

    def plan(self, request: Any) -> Any:
        from aura_agent.planning_bridge import PlanResult, PlanStep

        from aura.planning.models import Goal, Task

        granted = set(request.capabilities or [])
        tasks = [
            Task(
                name=f"actions.{name}",
                capability=f"actions.{name}",
                risk=0.05,
                estimated_cost=1.0,
                estimated_seconds=1.0,
            )
            for name in self._actions
            if f"actions.{name}" in granted
        ]
        if not tasks:
            return PlanResult(
                steps=[],
                valid=False,
                validation_errors=["no canonical action capability is granted to this agent"],
            )
        result = self._planning.plan(
            goal=Goal.create(description=request.goal), tasks=tasks
        )
        if result.primary is None:
            issues = "; ".join(result.issues or ("no valid canonical plan",))
            return PlanResult(steps=[], valid=False, validation_errors=[issues])
        steps = [
            PlanStep(
                tool_name=step.task.name,
                capability=step.task.capability,
                inputs={},
                expected_effects={"completed": True},
                description=f"canonical action {step.task.name}",
            )
            for step in result.primary.steps
        ]
        return PlanResult(steps=steps)


def canonical_action_tool(*, action_registry: Any, action_name: str, execution: Any) -> Any:
    """Expose one canonical action as a guarded agent tool.

    The agent's policy/safety/autonomy/budget gates run first; the tool then
    executes through the canonical :class:`ExecutionEngine` (guardrails,
    timeout, idempotency). Real failures raise far enough to be honest action
    failures -- never fabricated successes.
    """
    from aura_agent.contracts.errors import ToolExecutionError
    from aura_agent.tools.models import Tool

    spec = action_registry.get(action_name)

    def handler(inputs: dict[str, Any], *, context: Any) -> dict[str, Any]:
        from aura.execution.engine import ExecutionRequest
        from aura.execution.models import ActionInputs, WorldState

        request = ExecutionRequest(
            action=spec.name,
            inputs=ActionInputs(values=dict(inputs or {})),
            world_state=WorldState(values={}),
        )
        try:
            result = execution.execute(request)
        except Exception as exc:  # noqa: BLE001 - wrap into an honest failure
            raise ToolExecutionError(
                f"canonical action {action_name} failed: {type(exc).__name__}: {exc}"
            ) from exc
        primary = result.action_result
        if not result.ok:
            error = getattr(primary, "error", "") or "canonical action failed"
            raise ToolExecutionError(f"canonical action {action_name} failed: {error}")
        payload: dict[str, Any] = {
            "ok": True,
            "completed": True,
            "action": spec.name,
            "execution_id": str(result.request.execution_id),
        }
        if getattr(primary, "output", None):
            payload["output"] = primary.output
        return payload

    return Tool(
        name=f"actions.{action_name}",
        description=f"canonical AURA action {action_name!r} via guarded execution",
        input_schema={},
        capability=f"actions.{action_name}",
        permissions=(f"actions:{action_name}",),
        handler=handler,
        timeout_s=float(getattr(spec, "timeout_seconds", 30.0)) + 5.0,
    )


def _denial_class(exc: Exception) -> str:
    """Map an agent denial onto the execution failure vocabulary."""
    from aura_agent.contracts.errors import (
        ApprovalRequired,
        BudgetExceeded,
        CapabilityDenied,
        PermissionDenied,
        SafetyDenied,
    )

    if isinstance(exc, CapabilityDenied):
        return "capability"
    if isinstance(exc, PermissionDenied):
        return "permission"
    if isinstance(exc, SafetyDenied):
        return "safety"
    if isinstance(exc, ApprovalRequired):
        return "approval"
    if isinstance(exc, BudgetExceeded):
        return "resource"
    return "policy"
__all__ = [
    "AgentActionResult",
    "AgentTaskResult",
    "AgentsBridgeError",
    "CanonicalContext",
    "CanonicalPlanningProvider",
    "CanonicalReasoningProvider",
    "ResearchStageResult",
    "TaskEvaluation",
    "agents_available",
    "build_agent",
    "build_task_agent",
    "canonical_action_tool",
    "evaluate_task_outcome",
    "require_agents",
    "run_agent_action",
    "run_agent_task",
    "run_research_stage",
]