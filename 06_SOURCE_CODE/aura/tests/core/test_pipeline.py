"""Canonical pipeline integration tests.

These tests exercise the full end-to-end request flow in a deterministic,
safe environment: memory -> knowledge -> research -> reasoning -> planning ->
security -> execution -> observation -> verification -> reflection -> learning
-> memory update -> audit/trace/replay. No destructive action is ever executed;
all actions are inert, locally registered, and capability-gated.
"""

from __future__ import annotations

from aura.brain.engine import BrainEngine
from aura.core.pipeline import ExecutionPipeline, PipelineRequest, default_guardrails
from aura.execution.models import ActionSpec, make_result
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.planning.models import Goal, Task
from aura.reflection.models import SignalKind
from aura.security.permissions import Identity


def _inert_action(name: str, *, capability: str, ok: bool = True, risk: float = 0.1) -> ActionSpec:
    def handler(_inputs: object, _token: CancellationToken) -> object:
        if not ok:
            return make_result(ok=False, error=f"{name} failed")
        return make_result(ok=True, output={"done": name})

    return ActionSpec(
        name=name,
        capability=capability,
        handler=handler,
        risk=risk,
        expected_effects=("done",),
        timeout_seconds=5,
        declare_world_changes=True,
    )


def build_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register(_inert_action("write_report", capability="report.write"))
    registry.register(_inert_action("check_observatory", capability="observatory.check", ok=False))
    return registry


def build_pipeline(brain: BrainEngine | None = None) -> ExecutionPipeline:
    brain = brain or BrainEngine.create(seed=3)
    registry = build_registry()
    return ExecutionPipeline(
        brain=brain,
        registry=registry,
        guardrails=default_guardrails(registry),
    )
def test_full_canonical_flow_executes_permitted_action() -> None:
    brain = BrainEngine.create(seed=3)
    pipeline = build_pipeline(brain)
    goal = Goal.create(description="Research the topic and produce a report")
    task = Task(
        name="write_report",
        capability="report.write",
        estimated_cost=1.0,
        estimated_seconds=1.0,
        risk=0.1,
    )
    request = PipelineRequest(
        question="Is the deployment safe?",
        claims=("deployment requires approval",),
        goal=goal,
        tasks=(task,),
        action_inputs={"write_report": {"topic": "deployment"}},
        identity=Identity(id="tester", roles=("operator",)),
        world={"started": True},
    )
    result = pipeline.run(request)

    # full pipeline succeeded
    assert result.success
    assert result.research is not None
    assert result.plan is not None and result.plan.primary is not None
    assert len(result.executions) == 1
    assert result.executions[0].ok

    # security stage passed and was audited
    assert result.security_decisions[0]["allowed"]
    assert any(r.action == "report.write" for r in pipeline.audit.entries())

    # reflection ran and produced a review signal
    assert result.reflection is not None
    assert any(s.kind is SignalKind.SUCCESS_REVIEW for s in result.reflection.signals)

    # memory update recorded an episodic entry
    assert "episodic" in result.memory_ids
    entry = brain.memory.by_id(result.memory_ids["episodic"])  # type: ignore[arg-type]
    assert entry.content["success"] is True

    # the run is traceable and replayable through the flight recorder
    events = brain.recorder.events(execution_id=result.execution_id)
    assert any(e.event_type == "pipeline.started" for e in events)
    assert any(e.event_type == "pipeline.completed" for e in events)


def test_security_denies_action_without_capability() -> None:
    brain = BrainEngine.create(seed=3)
    pipeline = build_pipeline(brain)
    goal = Goal.create(description="Try a forbidden action")
    banned = Task(
        name="wipe_all",
        capability="admin.destructive",
        estimated_cost=1.0,
        risk=0.9,
    )
    request = PipelineRequest(
        question="Should I wipe everything?",
        goal=goal,
        tasks=(banned,),
        identity=Identity(id="operator"),
    )
    result = pipeline.run(request)

    # the ban is enforced: not allowed, never executed
    assert not result.success
    assert not result.security_decisions[0]["allowed"]
    assert result.executions == []
    # audit trail records the denial
    assert any(r.decision == "deny" for r in pipeline.audit.entries())
def test_failing_action_reflects_and_triggers_governed_learning() -> None:
    brain = BrainEngine.create(seed=3)
    pipeline = build_pipeline(brain)
    goal = Goal.create(description="Run the observatory check")
    task = Task(
        name="check_observatory",
        capability="observatory.check",
        estimated_cost=1.0,
        risk=0.1,
    )
    request = PipelineRequest(
        question="Is the observatory healthy?",
        goal=goal,
        tasks=(task,),
        identity=Identity(id="operator"),
    )
    result = pipeline.run(request)

    assert not result.success
    assert result.executions and not result.executions[0].ok

    # reflection produced a failure review and improvement suggestion
    assert result.reflection is not None
    kinds = {s.kind for s in result.reflection.signals}
    assert SignalKind.FAILURE_REVIEW in kinds

    # a poor outcome must produce a governed learning signal through the loop
    assert result.learning is not None


def test_reasoning_only_request_needs_no_execution() -> None:
    pipeline = build_pipeline()
    request = PipelineRequest(question="What is 2 + 2?", facts={"addition_is_defined": 0.9})
    result = pipeline.run(request)
    assert result.success
    assert result.plan is None
    assert result.executions == []
    assert result.reasoning["answer"] is not None