"""Execution domain tests: world-state isolation, guardrail pipeline, timeout, retry, idempotency."""

from __future__ import annotations

import time

from aura.execution.engine import ExecutionEngine, ExecutionRequest
from aura.execution.models import ActionInputs, ActionResult, ActionSpec, WorldState, make_result
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken, CancellationTokenSource
from aura.security.budgets import BudgetTracker
from aura.security.capabilities import Capability, CapabilityRegistry
from aura.security.guardrails import GuardrailService
from aura.security.permissions import Decision, PolicyEngine, Rule
from aura.security.safety import SafetyEvaluator


def build_engine(*, budget: BudgetTracker | None = None) -> ExecutionEngine:
    capabilities = CapabilityRegistry()
    capabilities.register(Capability(name="test.do"))
    policies = PolicyEngine()
    policies.add_rule(Rule(action="test.do", effect=Decision.ALLOW))
    guardrails = GuardrailService(
        capabilities=capabilities,
        policies=policies,
        safety=SafetyEvaluator(),
        budgets=budget or BudgetTracker(),
    )
    return ExecutionEngine(registry=ActionRegistry(), guardrails=guardrails)


def make_spec(
    *,
    handler=None,
    max_retries: int = 0,
    idempotent: bool = False,
    timeout_seconds: float = 5.0,
    risk: float = 0.0,
) -> ActionSpec:
    def _default(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del inputs, token
        return make_result(ok=True, output={"done": True})

    return ActionSpec(
        name="do",
        capability="test.do",
        handler=handler or _default,
        max_retries=max_retries,
        idempotent=idempotent,
        timeout_seconds=timeout_seconds,
        risk=risk,
    )


def test_action_success() -> None:
    engine = build_engine()
    engine._registry.register(make_spec())  # type: ignore[attr-defined]
    result = engine.execute(ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})))
    assert result.ok
    assert result.action_result.output == {"done": True}


def test_world_state_and_inputs_are_separate() -> None:
    captured: dict[str, object] = {}

    def handler(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        captured["inputs"] = inputs.to_dict()
        return make_result(ok=True, output={"world": inputs.get("world_only", None)})

    engine = build_engine()
    engine._registry.register(make_spec(handler=handler))  # type: ignore[attr-defined]
    engine.execute(
        ExecutionRequest(
            action="do",
            inputs=ActionInputs({"x": 1}),
            world_state=WorldState({"world_only": "secret"}),
        )
    )
    assert captured["inputs"] == {"x": 1}
    assert "world_only" not in captured["inputs"]


def test_missing_action_registry_raises_not_found() -> None:
    import pytest

    from aura.foundation.errors import NotFoundError

    engine = build_engine()
    with pytest.raises(NotFoundError):
        engine.execute(ExecutionRequest(action="missing", inputs=ActionInputs({}), world_state=WorldState({})))


def test_guardrail_denies_without_permission() -> None:
    capabilities = CapabilityRegistry()
    capabilities.register(Capability(name="test.public"))
    policies = PolicyEngine()  # default deny, no rules
    guardrails = GuardrailService(capabilities=capabilities, policies=policies)
    engine = ExecutionEngine(registry=ActionRegistry(), guardrails=guardrails)
    engine._registry.register(make_spec())  # type: ignore[attr-defined]
    result = engine.execute(ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})))
    assert not result.ok
    assert result.guardrail_stages
def test_timeout_bounds_execution() -> None:
    def slow(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del token
        time.sleep(5.0)
        return make_result(ok=True)

    engine = build_engine()
    engine._registry.register(make_spec(handler=slow, timeout_seconds=0.05))  # type: ignore[attr-defined]
    result = engine.execute(ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})))
    assert not result.ok
    assert "timeout" in result.action_result.error.lower()


def test_retry_recovers() -> None:
    state = {"calls": 0}

    def flaky(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del inputs, token
        state["calls"] += 1
        if state["calls"] < 3:
            raise RuntimeError("transient failure")
        return make_result(ok=True, output={"eventual": True})

    engine = build_engine()
    engine._registry.register(make_spec(handler=flaky, max_retries=3))  # type: ignore[attr-defined]
    result = engine.execute(ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})))
    assert result.ok
    assert result.attempts == 3


def test_retry_exhausted_fails() -> None:
    def always_fail(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del inputs, token
        raise RuntimeError("hard failure")

    engine = build_engine()
    engine._registry.register(make_spec(handler=always_fail, max_retries=1))  # type: ignore[attr-defined]
    result = engine.execute(ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})))
    assert not result.ok
    assert "hard failure" in result.action_result.error


def test_idempotent_replay_detection() -> None:
    calls = {"count": 0}

    def count(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del token
        calls["count"] += 1
        return make_result(ok=True)

    engine = build_engine()
    engine._registry.register(make_spec(handler=count, idempotent=True))  # type: ignore[attr-defined]
    request = ExecutionRequest(action="do", inputs=ActionInputs({"k": "v"}), world_state=WorldState({}))
    first = engine.execute(request)
    second = engine.execute(request)
    assert first.ok and second.ok
    assert second.replayed
    assert calls["count"] == 1


def test_cancellation_short_circuits() -> None:
    def handler(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del inputs
        token.check()
        return make_result(ok=True)

    engine = build_engine()
    engine._registry.register(make_spec(handler=handler))  # type: ignore[attr-defined]
    source = CancellationTokenSource()
    source.cancel()
    result = engine.execute(
        ExecutionRequest(action="do", inputs=ActionInputs({}), world_state=WorldState({})),
        cancellation=source.token,
    )
    assert not result.ok


def test_effects_update_world_state() -> None:
    def write(inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        del token
        return make_result(ok=True, output={"file": inputs.get("path")})

    engine = build_engine()
    engine._registry.register(ActionSpec(name="do", capability="test.do", handler=write, expected_effects=("file",)))  # type: ignore[attr-defined]
    result = engine.execute(
        ExecutionRequest(
            action="do",
            inputs=ActionInputs({"path": "/tmp/x"}),
            world_state=WorldState({"mode": "ro"}),
        )
    )
    assert result.new_world_state is not None
    assert result.new_world_state.get("mode") == "ro"  # world not implicitly mutated
    assert result.new_world_state.get("file") == "/tmp/x"