"""Failure-path and reliability integration tests for the execution pipeline.

Intentional, safe failures: timeout, handler failure with retries, malformed
tool result, precondition violation, cancellation, idempotent replay. Every
case asserts the system fails safely and observably (structured result, no
silent corruption).
"""

from __future__ import annotations

import time

from aura.execution.engine import ExecutionEngine, ExecutionRequest
from aura.execution.models import ActionSpec, ActionResult, WorldState, make_result
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken, CancellationTokenSource
from aura.foundation.ids import ExecutionId
from aura.core.pipeline import default_guardrails


def build_engine() -> tuple[ExecutionEngine, ActionRegistry]:
    registry = ActionRegistry()

    def ok_handler(_inputs: object, _token: CancellationToken) -> ActionResult:
        return make_result(ok=True, output={"done": True})

    def timeout_handler(_inputs: object, _token: CancellationToken) -> ActionResult:
        time.sleep(30)
        return make_result(ok=True, output={})

    def flaky_handler(inputs: object, _token: CancellationToken) -> ActionResult:
        values = getattr(inputs, "values", {})
        return make_result(ok=values.get("ok", False), error="flaky" if not values.get("ok", False) else "")

    def bad_result_handler(_inputs: object, _token: CancellationToken) -> object:
        return {"not": "an ActionResult"}

    def cancelled_handler(_inputs: object, token: CancellationToken) -> ActionResult:
        token.check()
        return make_result(ok=True, output={})

    registry.register(ActionSpec(name="ok", capability="test.ok", handler=ok_handler, expected_effects=("done",)))
    registry.register(ActionSpec(name="timeout", capability="test.timeout", handler=timeout_handler, timeout_seconds=0.1))
    registry.register(ActionSpec(name="flaky", capability="test.flaky", handler=flaky_handler, max_retries=2, timeout_seconds=1))
    registry.register(ActionSpec(name="bad_result", capability="test.bad", handler=bad_result_handler, max_retries=0))
    registry.register(ActionSpec(name="cancelled", capability="test.cancel", handler=cancelled_handler))
    engine = ExecutionEngine(registry=registry, guardrails=default_guardrails(registry))
    return engine, registry


def request(action: str, *, inputs: dict[str, object] | None = None, world: dict[str, object] | None = None) -> ExecutionRequest:
    from aura.execution.models import ActionInputs

    return ExecutionRequest(
        action=action,
        inputs=ActionInputs(values=inputs or {}),
        world_state=WorldState(values=world or {}),
        execution_id=ExecutionId.new(),
    )


def test_timeout_fails_safely() -> None:
    engine, _reg = build_engine()
    result = engine.execute(request("timeout"))
    assert not result.ok
    assert "timeout" in (result.action_result.error or "").lower()
    assert result.attempts == 1


def test_handler_failure_retries_then_fails() -> None:
    engine, _reg = build_engine()
    result = engine.execute(request("flaky", inputs={"ok": False}))
    assert not result.ok
    assert result.attempts == 3  # initial + 2 retries
    assert result.action_result.error
def test_handler_recovery_after_retry() -> None:
    calls: dict[str, int] = {}

    def flaky_then_ok(_inputs: object, _token: CancellationToken) -> ActionResult:
        calls["n"] = calls.get("n", 0) + 1
        if calls["n"] < 2:
            return make_result(ok=False, error="first attempt failed")
        return make_result(ok=True, output={"done": True})

    registry = ActionRegistry()
    registry.register(ActionSpec(name="recover", capability="test.recover", handler=flaky_then_ok, max_retries=1))
    engine = ExecutionEngine(registry=registry, guardrails=default_guardrails(registry))
    result = engine.execute(request("recover"))
    assert result.ok
    assert result.attempts == 2


def test_malformed_tool_result_blocked() -> None:
    engine, _reg = build_engine()
    result = engine.execute(request("bad_result"))
    assert not result.ok
    assert "ActionResult" in (result.action_result.error or "")


def test_cancellation_prevents_execution() -> None:
    engine, _reg = build_engine()
    source = CancellationTokenSource()
    source.cancel()
    result = engine.execute(request("cancelled"), cancellation=source.token)
    # The token check raises before the handler runs; the outcome is a clean
    # failure, never a partial world state.
    assert not result.ok


def test_idempotent_replay_is_deduplicated() -> None:
    registry = ActionRegistry()
    calls: dict[str, int] = {"n": 0}

    def counting_handler(_inputs: object, _token: CancellationToken) -> ActionResult:
        calls["n"] += 1
        return make_result(ok=True, output={"done": True})

    registry.register(ActionSpec(name="counted", capability="test.counted", handler=counting_handler, idempotent=True))
    engine = ExecutionEngine(registry=registry, guardrails=default_guardrails(registry))

    r1 = engine.execute(request("counted", inputs={"key": "a"}))
    r2 = engine.execute(request("counted", inputs={"key": "a"}))
    assert r1.ok and not r1.replayed
    assert r2.ok and r2.replayed
    assert calls["n"] == 1  # handler ran exactly once
def test_failure_is_observable_via_recorder() -> None:
    from aura.brain.engine import BrainEngine
    from aura.core.pipeline import ExecutionPipeline, default_guardrails, PipelineRequest
    from aura.planning.models import Goal, Task
    from aura.security.permissions import Identity

    def fail(_inputs: object, _token: CancellationToken) -> ActionResult:
        return make_result(ok=False, error="observable failure")

    registry = ActionRegistry()
    registry.register(ActionSpec(name="fail_action", capability="test.fail_action", handler=fail, expected_effects=("done",)))
    brain = BrainEngine.create(seed=5)
    pipeline = ExecutionPipeline(
        brain=brain,
        registry=registry,
        guardrails=default_guardrails(registry),
    )
    result = pipeline.run(
        PipelineRequest(
            question="run the failing action",
            goal=Goal.create(description="run one action"),
            tasks=(Task(name="fail_action", capability="test.fail_action", risk=0.1),),
            identity=Identity(id="reliability-test"),
        )
    )
    assert not result.success
    assert result.executions and not result.executions[0].ok
    events = pipeline.brain.recorder.events(execution_id=result.execution_id)
    assert any(e.event_type == "pipeline.action" for e in events)
    assert any(e.event_type == "pipeline.stage" and e.payload.get("stage") == "verification" for e in events)
    assert any(e.event_type == "pipeline.completed" for e in events)