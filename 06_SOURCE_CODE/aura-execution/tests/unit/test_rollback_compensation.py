"""Tests for rollback and compensation in aura-execution."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_execution import Capability, ExecutableAction, ExecutionRequest, ExecutionStatus
from aura_execution.orchestration.execution_engine import ExecutionEngine
from aura_execution.runtime.retries import RetryPolicy
from aura_execution.runtime.rollback import CompensationAction, CompensationRegistry, RollbackCoordinator


def _cap() -> Capability:
    return Capability("filesystem.write", frozenset({"write"}))


def _action(action_id="act-1", **kw) -> ExecutableAction:
    defaults = dict(
        name="write",
        capability="filesystem.write",
        inputs=["path", "text"],
        effects={"file_created": True},
        handler=lambda inputs, ctx: inputs["text"],
    )
    defaults.update(kw)
    return ExecutableAction(action_id, **defaults)


def test_rollback_restores_prior_state():
    coordinator = RollbackCoordinator()
    coordinator.register_undo("act-1", lambda state: {**state, "file_created": False})
    outcome = coordinator.rollback({"file_created": True}, action_ids=["act-1"])
    assert outcome.success is True
    assert "act-1" in outcome.rolled_back


def test_rollback_without_registered_undo_is_noop():
    coordinator = RollbackCoordinator()
    outcome = coordinator.rollback({"x": 1}, action_ids=["unknown"])
    assert outcome.success is True
    assert outcome.rolled_back == []


def test_compensation_action_runs_only_when_registered():
    calls = {"n": 0}
    registry = CompensationRegistry()
    registry.register(CompensationAction("act-1", lambda state: calls.__setitem__("n", calls["n"] + 1)))
    registry.compensate("act-1", {})
    assert calls["n"] == 1
    with pytest.raises(KeyError):
        registry.compensate("never-registered", {})


def test_execution_failure_triggers_compensation_after_non_retryable():
    compensated = {"flag": False}

    def always_fails(inputs, ctx):
        raise RuntimeError("invalid operation")

    engine = ExecutionEngine(retry_policy=RetryPolicy(max_retries=0))
    engine.register_capability(_cap())
    engine.compensations.register(
        CompensationAction("act-1", lambda state: compensated.__setitem__("flag", True))
    )
    result = engine.execute(ExecutionRequest(_action(handler=always_fails)))
    assert result.status is ExecutionStatus.FAILED
    assert compensated["flag"] is True


def test_finalized_failure_without_compensation_is_safe():
    def always_fails(inputs, ctx):
        raise RuntimeError("boom")

    engine = ExecutionEngine(retry_policy=RetryPolicy(max_retries=0))
    engine.register_capability(_cap())
    result = engine.execute(ExecutionRequest(_action(handler=always_fails)))
    assert result.status is ExecutionStatus.FAILED