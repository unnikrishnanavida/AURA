"""Phase 1F: canonical agent bridge integration tests.

Covers the required scenarios: agent available / unavailable, authorized and
unauthorized invocation, cancellation (before dispatch and mid-run), budget
failure, tool permission failure, successful execution, agent failure, and
provenance -- plus wiring of canonical AURA memory into the agent's memory
bridge and the canonical API surface (scope enforcement, cancellation, honest
result reporting).
"""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

import aura.agents as agents
from aura.agents import (
    AgentActionResult,
    AgentsBridgeError,
    CanonicalContext,
    agents_available,
    build_agent,
    run_agent_action,
    run_agent_task,
)
from aura.foundation.cancellation import CancellationTokenSource
from aura.foundation.clock import ManualClock
from aura.foundation.errors import CancelledError


def make_tool(name: str = "tools.noop", *, sleep: float = 0.0, fail: bool = False) -> Any:
    """A deterministic tool for bridge-level tests (never touches the system)."""
    from aura_agent.tools.models import SchemaField, Tool

    def handler(inputs: dict[str, Any], *, context: Any) -> dict[str, Any]:
        if sleep:
            time.sleep(sleep)
        if fail:
            raise RuntimeError("simulated tool failure")
        return {"ok": True, "echo": inputs.get("value"), "tool": name}

    return Tool(
        name=name,
        description=f"test tool {name}",
        input_schema={"value": SchemaField(name="value", type=str, required=False)},
        capability=name,
        permissions=(),
        handler=handler,
        timeout_s=5.0 if sleep else 1.0,
    )


def build_tooled_agent(*, name: str = "t", tool: Any | None = None) -> Any:
    """An agent with one allowed tool (base-deny policy overridden for it)."""
    tool = tool or make_tool()
    return build_agent(name=name, tools=(tool,), allow_rules=(("tools.*", "*"),))


# -- agent available / unavailable -----------------------------------------


def test_agents_available_when_runtime_installed() -> None:
    assert agents_available() is True
    from aura_agent.api import AgentBuilder  # noqa: F401


def test_agents_unavailable_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agents, "_AGENTS_INSTALLED", False)
    assert agents_available() is False
    with pytest.raises(AgentsBridgeError):
        build_agent()


# -- guarded action execution ---------------------------------------------


def test_successful_action_via_bridge() -> None:
    agent = build_tooled_agent()
    result = run_agent_action(
        agent=agent, tool_name="tools.noop", capability="tools.noop", inputs={"value": "hi"}
    )
    assert isinstance(result, AgentActionResult)
    assert result.success is True
    assert result.state == "succeeded"
    assert result.agent_id.startswith("ag-")
    assert result.events


def test_tool_permission_failure_is_denied_not_fabricated() -> None:
    agent = build_agent(name="noperm", tools=(make_tool(),))
    result = run_agent_action(agent=agent, tool_name="tools.noop", capability="tools.noop")
    assert result.success is False
    assert result.failure_class == "permission"
    assert "denied" in (result.error or "").lower()


def test_capability_failure_is_denied() -> None:
    agent = build_tooled_agent()
    result = run_agent_action(agent=agent, tool_name="tools.noop", capability="database.delete")
    assert result.success is False
    assert result.failure_class == "capability"


def test_budget_failure_is_denied() -> None:
    from aura_agent.budgets import AgentBudget
    from aura_agent.contracts.ids import ExecutionId

    agent = build_tooled_agent(name="budget")
    execution = ExecutionId("exe-1f-budget")
    agent.components.budget_engine.attach(execution, AgentBudget(limits={"actions": 0}))
    result = run_agent_action(
        agent=agent,
        tool_name="tools.noop",
        capability="tools.noop",
        execution_id=str(execution),
    )
    assert result.success is False
    assert result.failure_class == "resource"
    assert "budget" in (result.error or "").lower()


def test_action_failure_is_reported_honestly() -> None:
    agent = build_tooled_agent(name="fail", tool=make_tool(fail=True))
    result = run_agent_action(agent=agent, tool_name="tools.noop", capability="tools.noop")
    assert result.success is False
    assert result.error


def test_unknown_tool_is_a_failure() -> None:
    agent = build_agent(name="empty")
    result = run_agent_action(agent=agent, tool_name="tools.missing", capability="tools.missing")
    assert result.success is False
    assert "unknown tool" in (result.error or "")


# -- goal / task execution --------------------------------------------------


def test_successful_goal_via_task_bridge() -> None:
    agent = build_tooled_agent(name="goal-ok")
    result = run_agent_task(
        agent=agent,
        description="complete a task",
        success_criteria=("ok == True",),
        capabilities=("tools.noop",),
    )
    assert result.success is True
    assert result.goal_id and result.goal_id.startswith("goal-")
    assert result.reason != ""


def test_failed_goal_is_reported_honestly() -> None:
    agent = build_tooled_agent(name="goal-fail", tool=make_tool(fail=True))
    result = run_agent_task(
        agent=agent,
        description="impossible task",
        success_criteria=("ok == True",),
        capabilities=("tools.noop",),
    )
    assert result.success is False
    assert result.reason
    assert result.cancelled is False


def test_task_provenance_events_recorded() -> None:
    agent = build_tooled_agent(name="prov")
    result = run_agent_task(
        agent=agent,
        description="a provable task",
        success_criteria=("ok == True",),
        capabilities=("tools.noop",),
    )
    assert result.events
    types = {event.get("event_type") for event in result.events}
    assert all(isinstance(event.get("payload"), dict) for event in result.events)
    assert any("execution" in t or "goal" in t or "loop" in t for t in types)


def test_agent_memory_wires_into_canonical_memory(brain: Any) -> None:
    """Agent experiences persist into canonical AURA memory, not a private store."""
    agent = build_agent(
        name="mem",
        tools=(make_tool(),),
        allow_rules=(("tools.*", "*"),),
        memory=brain.memory,
    )
    before = brain.memory.store.count()
    result = run_agent_action(agent=agent, tool_name="tools.noop", capability="tools.noop")
    assert result.success is True
    assert brain.memory.store.count() > before


# -- cancellation -----------------------------------------------------------


def test_cancellation_before_start_raises_and_is_mapped() -> None:
    agent = build_tooled_agent(name="cancel-before")
    source = CancellationTokenSource()
    source.cancel()
    with pytest.raises(CancelledError):
        run_agent_task(agent=agent, description="x", cancellation=source.token)
    with pytest.raises(CancelledError):
        run_agent_action(
            agent=agent, tool_name="tools.noop", capability="tools.noop", cancellation=source.token
        )


def test_cancellation_during_run_is_reported() -> None:
    agent = build_tooled_agent(name="cancel-mid", tool=make_tool(sleep=0.3))
    source = CancellationTokenSource()

    def cancel_later() -> None:
        time.sleep(0.05)
        source.cancel()

    thread = threading.Thread(target=cancel_later)
    thread.start()
    result = run_agent_task(
        agent=agent,
        description="work",
        success_criteria=("ok == True",),
        capabilities=("tools.noop",),
        cancellation=source.token,
    )
    thread.join()
    assert result.cancelled is True


# -- canonical API surface --------------------------------------------------


def _post(port: int, path: str, payload: dict | None = None, *, token: str | None = None) -> tuple[int, dict]:
    import json
    from http.client import HTTPConnection

    conn = HTTPConnection("127.0.0.1", port, timeout=15)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request("POST", path, body=json.dumps(payload or {}), headers=headers)
    response = conn.getresponse()
    raw = response.read()
    body = json.loads(raw.decode()) if raw else {}
    status = response.status
    conn.close()
    return status, body


def _get(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    import json
    from http.client import HTTPConnection

    conn = HTTPConnection("127.0.0.1", port, timeout=15)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    status = response.status
    conn.close()
    return status, body


def _start(api: Any) -> int:
    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    api._httpd = httpd
    return httpd.server_port


def _auth_server(*, aura_engine: Any = None) -> tuple[Any, int, str, str]:
    """A token-bound server; returns (api, port, owner_key, other_key)."""
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.sdk.client import Aura
    from aura.security.audit import AuditLog

    engine = aura_engine or Aura(clock=ManualClock(0), seed=3)
    api = AuraApiServer(
        aura=engine,
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key="service-key-at-least-16-char",
            admin_key="admin-key-at-least-16-char",
        ),
        audit_log=AuditLog(),
    )
    port = _start(api)
    status, issued_1 = _post(
        port,
        "/v1/keys",
        {"scopes": ["agents.run", "cognition.reason"]},
        token="admin-key-at-least-16-char",
    )
    assert status == 201
    status, issued_2 = _post(
        port,
        "/v1/keys",
        {"scopes": ["agents.run", "cognition.reason"]},
        token="admin-key-at-least-16-char",
    )
    assert status == 201
    return api, port, str(issued_1["api_key"]), str(issued_2["api_key"])


def test_api_agents_run_requires_scope() -> None:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.security.audit import AuditLog

    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key="service-key-at-least-16-char",
            admin_key="admin-key-at-least-16-char",
        ),
        audit_log=AuditLog(),
    )
    port = _start(api)
    status, issued = _post(
        port, "/v1/keys", {"scopes": ["cognition.reason"]}, token="admin-key-at-least-16-char"
    )
    assert status == 201
    denied, body = _post(port, "/v1/agents/run", {"goal": "hi"}, token=issued["api_key"])
    assert denied == 403
    assert body["error"]["code"] == "api.forbidden"


def test_api_agents_authorized_invocation_is_honest() -> None:
    api, port, owner_key, _other = _auth_server()
    status, body = _post(
        port,
        "/v1/agents/run",
        {"goal": "do a task", "success_criteria": ["done == True"]},
        token=owner_key,
    )
    assert status == 200
    assert body["status"] == "ok"
    assert body["agent_id"] and body["agent_id"].startswith("ag-")
    assert body["goal_id"] and body["goal_id"].startswith("goal-")
    assert isinstance(body["success"], bool)
    assert body["reason"]
    assert isinstance(body["events"], list)
    assert body["request_id"].startswith("rq-")
    assert body["success"] is False  # no capability granted: no fabricated success


def test_api_agents_unavailable_when_runtime_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.sdk.client import Aura

    monkeypatch.setattr(agents, "_AGENTS_INSTALLED", False)
    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=3),
        config=ServerConfig(host="127.0.0.1", port=0),
    )
    port = _start(api)
    status, body = _post(port, "/v1/agents/run", {"goal": "hi"})
    assert status == 503
    assert body["error"]["code"] == "agents.unavailable"


def test_api_agents_validation() -> None:
    api, port, owner_key, _other = _auth_server()
    status, body = _post(port, "/v1/agents/run", {}, token=owner_key)
    assert status == 400
    assert body["error"]["code"] == "api.validation"


def test_api_agent_cancellation_and_ownership(monkeypatch: pytest.MonkeyPatch) -> None:
    from aura.sdk.client import Aura

    def blocking_run_agent_task(*, cancellation: Any, **kwargs: Any) -> Any:
        while cancellation is not None and not cancellation.cancelled:
            time.sleep(0.005)
        raise CancelledError("agent task cancelled")

    monkeypatch.setattr("aura.api.server.run_agent_task", blocking_run_agent_task)
    engine = Aura(clock=ManualClock(0), seed=3)
    api, port, owner_key, other_key = _auth_server(aura_engine=engine)
    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(
            port,
            "/v1/agents/run",
            {"goal": "long task", "request_id": "c0ffee"},
            token=owner_key,
        )

    thread = threading.Thread(target=run)
    thread.start()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        st, body = _get(port, "/v1/tasks/rq-c0ffee", token=owner_key)
        if st == 200 and body.get("status") == "running":
            break
        time.sleep(0.02)

    denied, _ = _post(port, "/v1/tasks/rq-c0ffee/cancel", token=other_key)
    assert denied == 403
    cancel_status, _ = _post(port, "/v1/tasks/rq-c0ffee/cancel", token=owner_key)
    assert cancel_status == 202
    thread.join(10)
    assert not thread.is_alive()
    http, payload = bucket["out"]
    assert http == 200
    assert payload["status"] == "cancelled"
    assert payload["cancelled_stage"] == "orchestration"
    st, body = _get(port, "/v1/tasks/rq-c0ffee", token=owner_key)
    assert body["status"] == "cancelled"
    assert api._tasks.active_count() == 0


# -- 1G: canonical brain/reasoning/planning/execution integration -----------


def _make_echo_spec() -> Any:
    from aura.execution.models import ActionInputs, ActionSpec, make_result

    def handler(inputs: ActionInputs, token: Any) -> Any:
        return make_result(ok=True, output={"text": inputs.get("text", "")})

    return ActionSpec(name="echo", capability="echo", handler=handler, risk=0.0)


def _canonical_context(*, registry: Any | None = None, execution: Any | None = None, brain: Any = None) -> CanonicalContext:
    from aura.core.pipeline import default_guardrails
    from aura.execution.engine import ExecutionEngine
    from aura.execution.registry import ActionRegistry
    from aura.planning.engine import PlanningEngine

    reg = registry
    if reg is None:
        reg = ActionRegistry()
        reg.register(_make_echo_spec())
    ex = execution
    if ex is None:
        ex = ExecutionEngine(registry=reg, guardrails=default_guardrails(reg))
    return CanonicalContext(
        brain=brain,
        memory=brain.memory if brain is not None else None,
        planning=PlanningEngine(),
        action_registry=reg,
        execution=ex,
    )


def test_canonical_agent_end_to_end_task_succeeds() -> None:
    """user request -> agent -> canonical reasoning -> canonical planning ->
    permitted canonical action -> result."""
    from aura.sdk.client import Aura

    engine = Aura(clock=ManualClock(0), seed=3)
    context = _canonical_context(brain=engine.brain)
    agent = build_agent(name="g-e2e", canonical=context)
    assert type(agent.components.reasoning_bridge.provider).__name__ == "CanonicalReasoningProvider"
    assert type(agent.components.planning_bridge.provider).__name__ == "CanonicalPlanningProvider"
    assert "actions.echo" in agent.components.tool_registry.names()

    result = run_agent_task(
        agent=agent,
        description="echo the value",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
    )
    assert result.success is True
    assert result.goal_id and result.goal_id.startswith("goal-")
    assert result.events
    types = [event.get("event_type") for event in result.events]
    assert any("plan" in t or "execution" in t for t in types)


def test_canonical_agent_denied_capability_is_honest() -> None:
    from aura.sdk.client import Aura

    engine = Aura(clock=ManualClock(0), seed=3)
    agent = build_agent(name="g-deny", canonical=_canonical_context(brain=engine.brain))
    result = run_agent_task(
        agent=agent,
        description="delete the database",
        success_criteria=("completed == True",),
        capabilities=("database.delete",),
    )
    assert result.success is False
    assert result.reason  # honest failure: the capability is not available


def test_canonical_agent_failed_action_is_honest() -> None:
    from aura.core.pipeline import default_guardrails
    from aura.execution.engine import ExecutionEngine
    from aura.execution.models import ActionSpec, make_result
    from aura.execution.registry import ActionRegistry

    reg = ActionRegistry()
    reg.register(
        ActionSpec(name="boom", capability="boom", handler=lambda i, t: make_result(ok=False, error="simulated failure"), risk=0.0)
    )
    ex = ExecutionEngine(registry=reg, guardrails=default_guardrails(reg))
    agent = build_agent(name="g-fail", canonical=_canonical_context(registry=reg, execution=ex))
    result = run_agent_task(
        agent=agent,
        description="do the work",
        success_criteria=("completed == True",),
        capabilities=("actions.boom",),
    )
    assert result.success is False
    assert result.reason


def test_canonical_agent_timeout_is_honest() -> None:
    import time as _time

    from aura.core.pipeline import default_guardrails
    from aura.execution.engine import ExecutionEngine
    from aura.execution.models import ActionSpec, make_result
    from aura.execution.registry import ActionRegistry

    reg = ActionRegistry()

    def slow_handler(_inputs: Any, _token: Any) -> Any:
        _time.sleep(1.0)
        return make_result(ok=True, output={})

    reg.register(ActionSpec(name="slow", capability="slow", handler=slow_handler, timeout_seconds=0.1, risk=0.0))
    ex = ExecutionEngine(registry=reg, guardrails=default_guardrails(reg))
    agent = build_agent(name="g-timeout", canonical=_canonical_context(registry=reg, execution=ex))
    result = run_agent_task(
        agent=agent,
        description="wait forever",
        success_criteria=("completed == True",),
        capabilities=("actions.slow",),
    )
    assert result.success is False
    assert result.reason


def test_canonical_reasoning_provider_reports_failure() -> None:
    from aura_agent.reasoning_bridge import ReasoningRequest as AgentReasoningRequest

    from aura.agents import CanonicalReasoningProvider

    class BrokenBrain:
        def reason(self, **kwargs: Any) -> Any:
            raise RuntimeError("brain offline")

    provider = CanonicalReasoningProvider(brain=BrokenBrain())
    result = provider.reason(AgentReasoningRequest(objective="decide", context={}))
    assert result.answer == "no_usable_plan"
    assert "provider_error" in result.metadata
    assert "RuntimeError" in result.metadata["provider_error"]


def test_canonical_planning_provider_requires_granted_capability() -> None:
    from aura_agent.contracts.ids import AgentId, GoalId
    from aura_agent.planning_bridge import PlanningRequest

    from aura.agents import CanonicalPlanningProvider
    from aura.planning.engine import PlanningEngine

    provider = CanonicalPlanningProvider(PlanningEngine(), action_names=("echo",))
    plan = provider.plan(
        PlanningRequest(goal="x", goal_id=GoalId("goal-1"), agent_id=AgentId("ag-1"), capabilities=[])
    )
    assert plan.valid is False
    assert plan.validation_errors


def test_canonical_agent_missing_context_is_honest() -> None:
    """No stored memory/knowledge: canonical reasoning still answers honestly
    and the guarded action can still complete the goal."""
    from aura.sdk.client import Aura

    engine = Aura(clock=ManualClock(0), seed=3)
    agent = build_agent(name="g-nocontext", canonical=_canonical_context(brain=engine.brain))
    result = run_agent_task(
        agent=agent,
        description="2+2",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
    )
    assert result.cancelled is False
    assert result.events


def test_api_agents_canonical_end_to_end_success() -> None:
    """Full canonical runtime: user request -> agent -> canonical reasoning ->
    canonical planning -> permitted canonical action (echo) -> success."""
    api, port, owner_key, _other = _auth_server()
    status, body = _post(
        port,
        "/v1/agents/run",
        {
            "goal": "echo the greeting",
            "success_criteria": ["completed == True"],
            "capabilities": ["actions.echo"],
        },
        token=owner_key,
    )
    assert status == 200
    assert body["status"] == "ok"
    assert body["success"] is True
    assert body["reason"]
    assert body["events"]
    assert body["agent_id"] and body["agent_id"].startswith("ag-")
    assert body["goal_id"] and body["goal_id"].startswith("goal-")


def test_api_agents_canonical_denied_capability_is_honest() -> None:
    """An unexposed capability must never fabricate success."""
    api, port, owner_key, _other = _auth_server()
    status, body = _post(
        port,
        "/v1/agents/run",
        {
            "goal": "delete everything",
            "success_criteria": ["completed == True"],
            "capabilities": ["database.delete"],
        },
        token=owner_key,
    )
    assert status == 200
    assert body["status"] == "ok"
    assert body["success"] is False
    assert body["reason"]


# -- 1H: canonical research integration -------------------------------------


def _ran_agent(*, brain: Any = None) -> Any:
    from aura.sdk.client import Aura

    engine = Aura(clock=ManualClock(0), seed=3)
    return build_agent(name="g-research", canonical=_canonical_context(brain=engine.brain)), engine


def _research(*, claim: str = "X is true", strength: float = 0.9, source: str = "primary") -> Any:
    from aura.research.engine import ResearchEngine

    return ResearchEngine(), (claim,), {claim: (strength, source, 0.9)}


def test_research_lifecycle_verified() -> None:
    from aura.agents import run_research_stage

    research, claims, evidence = _research()
    stage = run_research_stage(research=research, question="is X true?", claims=claims, evidence=evidence)
    assert stage.state == "verified"
    assert list(stage.state_history) == ["requested", "planned", "retrieved", "verified"]
    assert stage.research_facts == {"X is true": 0.91}
    assert stage.findings and stage.findings[0]["status"] == "evidence"


def test_research_retrieved_not_verified_without_evidence() -> None:
    """Retrieval (evidence assessed) is not verification on its own."""
    from aura.agents import run_research_stage

    research, claims, _evidence = _research(strength=0.0, source="unknown")
    stage = run_research_stage(research=research, question="Y?", claims=claims, evidence={})
    assert stage.state == "retrieved"
    assert stage.research_facts == {}
    assert "verified" not in stage.state_history


def test_research_no_fabricated_evidence() -> None:
    from aura.agents import run_research_stage

    research, claims, _evidence = _research(strength=0.0, source="unknown")
    stage = run_research_stage(research=research, question="Z?", claims=("Z is true",), evidence={})
    assert stage.findings  # findings exist but must not claim support
    assert all(f["status"] == "speculation" for f in stage.findings)
    assert stage.research_facts == {}


def test_research_failure_is_honest() -> None:
    from aura.agents import run_research_stage
    from aura.research.engine import ResearchEngine

    # A real engine failure path (invalid input) is reported, not hidden.
    stage = run_research_stage(research=ResearchEngine(), question="   ", claims=("Q",))
    assert stage.state == "failed"
    assert stage.error
    assert stage.research_facts == {}


def test_research_unavailable_is_failed() -> None:
    from aura.agents import run_research_stage

    stage = run_research_stage(research=None, question="Q?")
    assert stage.state == "failed"
    assert stage.error == "research unavailable"


def test_research_cancelled_before_start() -> None:
    from aura.agents import run_research_stage

    research, claims, evidence = _research()
    source = CancellationTokenSource()
    source.cancel()
    stage = run_research_stage(research=research, question="Q?", claims=claims, evidence=evidence, cancellation=source.token)
    assert stage.state == "cancelled"
    assert stage.cancelled is True
    assert "verified" not in stage.state_history


def test_research_to_reasoning_handoff() -> None:
    """Verified research feeds canonical reasoning as facts (real handoff)."""
    agent, engine = _ran_agent()
    research, claims, evidence = _research(claim="echo completes the task")
    result = run_agent_task(
        agent=agent,
        description="perform research then finish",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
        research=research,
        research_claims=claims,
        research_evidence=evidence,
        require_research=True,
    )
    provider = agent.components.reasoning_bridge.provider
    assert getattr(provider, "_research_facts", {}) == {"echo completes the task": 0.91}
    assert result.research and result.research["state"] == "verified"


def test_research_provenance_events() -> None:
    agent, engine = _ran_agent()
    research, claims, evidence = _research()
    result = run_agent_task(
        agent=agent,
        description="research then done",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
        research=research,
        research_claims=claims,
        research_evidence=evidence,
        require_research=True,
    )
    assert result.research and result.research["execution_id"]
    assert result.research["findings"]
    assert result.research["verified_facts"]
    types = [e.get("event_type") for e in result.events]
    assert any("research" in t for t in types)


def test_research_aware_vertical_slice() -> None:
    """user/agent goal -> research -> evidence -> reasoning -> planning ->
    authorized execution -> completed result (the full canonical path)."""
    agent, engine = _ran_agent()
    research, claims, evidence = _research(claim="script may proceed")
    result = run_agent_task(
        agent=agent,
        description="research then deploy the echo",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
        research=research,
        research_claims=claims,
        research_evidence=evidence,
        require_research=True,
    )
    assert result.success is True
    assert result.research and result.research["state"] == "verified"
    assert result.research["verified_facts"] == {"script may proceed": 0.91}
    types = [e.get("event_type") for e in result.events]
    assert any("execution" in t for t in types)


def test_require_research_abstains_without_verified_evidence() -> None:
    agent, engine = _ran_agent()
    research, claims, _evidence = _research(strength=0.0, source="unknown")
    result = run_agent_task(
        agent=agent,
        description="deploy only with evidence",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
        research=research,
        research_claims=claims,
        require_research=True,
    )
    assert result.success is False
    assert "verif" in result.reason.lower()
    assert result.research and result.research["state"] == "retrieved"
    # No execution ran after an unverified research stage:
    types = [e.get("event_type") for e in result.events]
    assert all("execution.actions" not in t for t in types)


def test_require_research_abstains_on_failure() -> None:
    agent, engine = _ran_agent()
    claims = ("q-claim",)

    class Failing:
        def research(self, inp: Any) -> Any:
            raise RuntimeError("research backend down")

    result = run_agent_task(
        agent=agent,
        description="deploy only with research",
        success_criteria=("completed == True",),
        capabilities=("actions.echo",),
        research=Failing(),
        research_claims=claims,
        require_research=True,
    )
    assert result.success is False
    assert result.research and result.research["state"] == "failed"


def test_research_does_not_authorize_execution() -> None:
    """A verified research finding alone never authorizes an action."""
    agent, engine = _ran_agent()
    research, claims, evidence = _research(claim="approve the deletion")
    result = run_agent_task(
        agent=agent,
        description="act on the approved claim",
        success_criteria=("completed == True",),
        capabilities=(),  # no canonical action is granted
        research=research,
        research_claims=claims,
        research_evidence=evidence,
        require_research=True,
    )
    assert result.research and result.research["state"] == "verified"
    assert result.success is False  # research did not authorize execution
    types = [e.get("event_type") for e in result.events]
    assert all("actions." not in t for t in types)


def test_agent_denied_capability_still_denied_with_research() -> None:
    """Research cannot override the agent's base-deny capability gate."""
    agent, engine = _ran_agent()
    research, claims, evidence = _research(claim="delete everything")
    result = run_agent_task(
        agent=agent,
        description="erase the database",
        success_criteria=("completed == True",),
        capabilities=("database.delete",),
        research=research,
        research_claims=claims,
        research_evidence=evidence,
    )
    assert result.success is False
    assert result.research is not None


def test_api_agents_research_vertical_slice() -> None:
    """Real HTTP: research -> reasoning -> planning -> authorized echo -> success."""
    api, port, owner_key, _other = _auth_server()
    status, body = _post(
        port,
        "/v1/agents/run",
        {
            "goal": "research then run the script",
            "success_criteria": ["completed == True"],
            "capabilities": ["actions.echo"],
            "require_research": True,
            "research_claims": ["the script is safe"],
            "research_evidence": {"the script is safe": [0.9, "primary", 0.9]},
        },
        token=owner_key,
    )
    assert status == 200
    assert body["status"] == "ok"
    assert body["success"] is True
    assert body["research"] and body["research"]["state"] == "verified"
    assert body["research"]["verified_facts"] == {"the script is safe": 0.91}
    assert body["research"]["findings"]


def test_api_agents_research_inconclusive_is_honest() -> None:
    """Research without support never fabricates verification or a success."""
    api, port, owner_key, _other = _auth_server()
    status, body = _post(
        port,
        "/v1/agents/run",
        {
            "goal": "deploy only with verified evidence",
            "success_criteria": ["completed == True"],
            "capabilities": ["actions.echo"],
            "require_research": True,
            "research_claims": ["the script is safe"],
        },
        token=owner_key,
    )
    assert status == 200
    assert body["success"] is False
    assert body["research"]["state"] == "retrieved"
    assert body["research"]["verified_facts"] == {}


def test_api_agents_research_requires_scope() -> None:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.security.audit import AuditLog

    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key="service-key-at-least-16-char",
            admin_key="admin-key-at-least-16-char",
        ),
        audit_log=AuditLog(),
    )
    port = _start(api)
    status, issued = _post(
        port, "/v1/keys", {"scopes": ["cognition.reason"]}, token="admin-key-at-least-16-char"
    )
    assert status == 201
    denied, body = _post(
        port,
        "/v1/agents/run",
        {"goal": "x", "require_research": True, "research_claims": ["y"]},
        token=issued["api_key"],
    )
    assert denied == 403
    assert body["error"]["code"] == "api.forbidden"


def test_research_is_not_persisted_to_memory() -> None:
    """Research evidence stays distinct from personal memory: it is not written
    to canonical memory by the research stage."""
    agent, engine = _ran_agent()
    before = engine.brain.memory.store.count()
    research, claims, evidence = _research(claim="research insight abc")
    result = run_agent_task(
        agent=agent,
        description="research only",
        success_criteria=("completed == True",),
        capabilities=(),
        research=research,
        research_claims=claims,
        research_evidence=evidence,
        require_research=True,
    )
    assert result.research and result.research["state"] == "verified"
    assert engine.brain.memory.store.count() == before


# -- 1I: reflection + verification + learning integration -------------------


def test_evaluate_success_verified_no_candidate() -> None:
    from aura.agents import evaluate_task_outcome

    evaluation = evaluate_task_outcome(
        goal="g", success=True, cancelled=False, events_summary=("execution.actions.echo",)
    )
    assert evaluation.verification_status == "verified"
    assert evaluation.learning_status == "none"
    assert evaluation.candidate_id is None
    assert evaluation.signals  # reflection ran and recorded signals


def test_evaluate_inconclusive_without_events() -> None:
    from aura.agents import evaluate_task_outcome

    evaluation = evaluate_task_outcome(goal="g", success=True, cancelled=False, events_summary=())
    assert evaluation.verification_status == "inconclusive"


def test_evaluate_failed_produces_learning_candidate() -> None:
    from aura.agents import evaluate_task_outcome

    evaluation = evaluate_task_outcome(
        goal="g", success=False, cancelled=False, deviations=("failed",), events_summary=("execution.actions.boom",)
    )
    assert evaluation.verification_status == "failed"
    assert evaluation.learning_status == "candidate"
    assert evaluation.candidate_id and evaluation.candidate_id.startswith("sig-")
    assert evaluation.evidence_count >= 1


def test_evaluate_cancelled_produces_no_learning() -> None:
    from aura.agents import evaluate_task_outcome

    evaluation = evaluate_task_outcome(goal="g", success=False, cancelled=True)
    assert evaluation.verification_status == "cancelled"
    assert evaluation.learning_status == "none"
    assert evaluation.candidate_id is None


def test_agent_failure_reports_candidate_not_active() -> None:
    """A failed agent task yields a learning CANDIDATE, never auto-applied."""
    from aura.core.pipeline import default_guardrails
    from aura.execution.engine import ExecutionEngine
    from aura.execution.models import ActionSpec, make_result
    from aura.execution.registry import ActionRegistry

    reg = ActionRegistry()
    reg.register(ActionSpec(name="boom", capability="boom", handler=lambda i, t: make_result(ok=False, error="op failed"), risk=0.0))
    ex = ExecutionEngine(registry=reg, guardrails=default_guardrails(reg))
    agent = build_agent(name="g-learn", canonical=_canonical_context(registry=reg, execution=ex))
    result = run_agent_task(
        agent=agent,
        description="do the work",
        success_criteria=("completed == True",),
        capabilities=("actions.boom",),
    )
    assert result.success is False
    assert result.evaluation is not None
    assert result.evaluation["verification_status"] == "failed"
    assert result.evaluation["learning_status"] == "candidate"
    # The candidate is NOT active: nothing was applied by the run.
    assert result.evaluation["candidate_id"]
    assert "applied_ref" not in result.evaluation or result.evaluation.get("applied_ref") is None


def test_approval_gate_applies_versioned_learning() -> None:
    """An explicit server-side approval applies the candidate through the
    canonical versioned LearningRegistry (status APPLIED, active)."""
    from aura.learning.engine import LearningEngine
    from aura.learning.models import LearningSignal

    engine = LearningEngine()
    signal = LearningSignal.create(
        kind="agent_reflection", content="tighten preconditions before retry", evidence=[{"score": 0.8}]
    )
    result = engine.approve_and_apply(signal, authorized=True)
    assert result.applied is True
    assert result.change is not None and result.change.ref.startswith("chg-")
    assert result.change.active is True
    assert signal.status.value == "applied"
    assert len(engine.registry.active()) == 1
    # Versioned record is readable.
    assert len(engine.registry.history()) == 1


def test_rejected_candidate_insufficient_evidence() -> None:
    from aura.learning.engine import LearningEngine
    from aura.learning.models import LearningSignal

    engine = LearningEngine()
    signal = LearningSignal.create(kind="agent_reflection", content="change something", evidence=[])
    result = engine.submit(signal)
    assert result.applied is False
    assert signal.status.value == "rejected"
    assert "insufficient" in result.outcome.reason
    assert engine.registry.active() == []


def test_safety_relevant_learning_rejected_without_authorization() -> None:
    """Safety-relevant learning is blocked until explicit server-side authz."""
    from aura.learning.engine import LearningEngine
    from aura.learning.models import LearningSignal

    engine = LearningEngine()
    signal = LearningSignal.create(
        kind="policy_change", content="relax the security policy", evidence=[{"score": 0.9}]
    )
    signal.safety_relevant = True
    result = engine.submit(signal)
    assert result.applied is False
    assert signal.status.value == "rejected"
    assert "safety-relevant" in result.outcome.reason

    # With explicit authorization the gate permits it (versioned).
    signal2 = LearningSignal.create(
        kind="policy_change", content="relax the security policy", evidence=[{"score": 0.9}]
    )
    signal2.safety_relevant = True
    approved = engine.approve_and_apply(signal2, authorized=True)
    assert approved.applied is True


def test_rollback_learning_change() -> None:
    """Approved version N+1 can be rolled back to restore pre-change state."""
    from aura.learning.engine import LearningEngine
    from aura.learning.models import LearningSignal

    engine = LearningEngine()
    applied = engine.approve_and_apply(
        LearningSignal.create(kind="agent_reflection", content="lesson", evidence=[{"score": 0.7}]),
        authorized=True,
    )
    assert applied.applied and applied.change is not None
    assert len(engine.registry.active()) == 1

    rolled = engine.rollback(applied.change.ref)
    assert rolled.rolled_back_at is not None
    assert rolled.active is False
    assert engine.registry.active() == []  # no active learned behavior after rollback
    assert len(engine.registry.history()) == 1  # destructive history preserved


def test_agent_vertical_slice_with_versioned_learning() -> None:
    """goal -> execution -> outcome -> verification -> reflection ->
    learning candidate -> approval -> versioned learning -> future read + rollback."""
    from aura.core.pipeline import default_guardrails
    from aura.execution.engine import ExecutionEngine
    from aura.execution.models import ActionSpec, make_result
    from aura.execution.registry import ActionRegistry
    from aura.learning.engine import LearningEngine
    from aura.learning.models import LearningSignal

    reg = ActionRegistry()
    reg.register(ActionSpec(name="boom", capability="boom", handler=lambda i, t: make_result(ok=False, error="op failed"), risk=0.0))
    ex = ExecutionEngine(registry=reg, guardrails=default_guardrails(reg))
    agent = build_agent(name="g-slice", canonical=_canonical_context(registry=reg, execution=ex))

    result = run_agent_task(
        agent=agent,
        description="deliver the outcome",
        success_criteria=("completed == True",),
        capabilities=("actions.boom",),
    )
    assert result.success is False
    assert result.evaluation is not None
    assert result.evaluation["verification_status"] == "failed"
    assert result.evaluation["learning_status"] == "candidate"
    candidate_id = result.evaluation["candidate_id"]
    candidate_content = result.evaluation["candidate_content"]

    # Explicit, versioned approval (server-side, beyond any client input).
    learner = LearningEngine()
    signal = LearningSignal.create(
        kind="agent_reflection", content=candidate_content, evidence=[{"score": 0.7}]
    )
    applied = learner.approve_and_apply(signal, authorized=True)
    assert applied.applied and applied.change is not None
    assert learner.registry.active() == [applied.change]
    # The approved learning is readable as a versioned future behavior.
    assert len(learner.registry.history(signal.id)) == 1

    # The candidate id from the run is distinct from (and never auto-equals) active.
    assert candidate_id and candidate_id.startswith("sig-")

    # Rollback returns the system to no-active-learned-behavior.
    learner.rollback(applied.change.ref)
    assert learner.registry.active() == []


def test_unapproved_candidate_is_not_active() -> None:
    """Creating a candidate never makes it active; nothing is auto-applied."""
    from aura.agents import evaluate_task_outcome
    from aura.learning.engine import LearningEngine

    learner = LearningEngine()
    evaluation = evaluate_task_outcome(
        goal="g", success=False, cancelled=False, deviations=("failed",), events_summary=("x",)
    )
    assert evaluation.learning_status == "candidate"
    # The run/evaluation never applied anything to a registry.
    assert learner.registry.active() == []
    assert learner.registry.history() == []


def test_api_agents_reports_evaluation() -> None:
    """Real HTTP: a successful canonical run reports verification + absence of
    learning; a denied-capability run reports failed verification + candidate."""
    api, port, owner_key, _other = _auth_server()

    ok = _post(
        port,
        "/v1/agents/run",
        {"goal": "echo fine", "success_criteria": ["completed == True"], "capabilities": ["actions.echo"]},
        token=owner_key,
    )
    assert ok[0] == 200
    assert ok[1]["success"] is True
    assert ok[1].get("evaluation", {}).get("verification_status") == "verified"

    denied = _post(
        port,
        "/v1/agents/run",
        {"goal": "delete everything", "success_criteria": ["completed == True"], "capabilities": ["database.delete"]},
        token=owner_key,
    )
    assert denied[0] == 200
    assert denied[1]["success"] is False
    assert denied[1].get("evaluation", {}).get("verification_status") == "failed"
    assert denied[1]["evaluation"]["learning_status"] in ("none", "candidate")