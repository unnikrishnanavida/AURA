"""Tests for aura-execution runtime guarantees: timeout, cancellation, retries,
idempotency, approval rejection, dry run."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_execution import Capability, ExecutableAction, ExecutionRequest, ExecutionStatus
from aura_execution.orchestration.execution_engine import ExecutionEngine
from aura_execution.runtime.cancellation import CancellationToken, Cancelled
from aura_execution.runtime.dry_run import DryRunMode
from aura_execution.runtime.retries import RetryClass, RetryClassifier, RetryPolicy
from aura_execution.runtime.timeouts import TimeoutError, TimeoutGuard


def _cap(name="filesystem.write", operations=frozenset({"write"})) -> Capability:
    return Capability(name, operations)


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


def test_timeout_guard_raises_when_budget_exceeded():
    guard = TimeoutGuard(timeout=0.001)
    with pytest.raises(TimeoutError):
        guard.run(lambda *a, **k: time.sleep(0.02))


def test_timeout_guard_passes_within_budget():
    guard = TimeoutGuard(timeout=1.0)
    elapsed, value = guard.run(lambda: 42)
    assert value == 42
    assert elapsed >= 0.0


def test_cancellation_token_fails_closed():
    token = CancellationToken()
    token.cancel("operator abort")
    assert token.cancelled is True
    with pytest.raises(Cancelled):
        token.check()


def test_cancelled_execution_returns_cancelled():
    engine = ExecutionEngine()
    engine.register_capability(_cap())
    token = CancellationToken()
    token.cancel("pre-cancelled")
    result = engine.execute(ExecutionRequest(_action()), token=token)
    assert result.status is ExecutionStatus.CANCELLED


def test_retryable_failure_is_retried():
    calls = {"n": 0}

    def flaky(inputs, ctx):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("temporary connection reset")
        return "recovered"

    engine = ExecutionEngine(retry_policy=RetryPolicy(max_retries=3, backoff_seconds=0.0))
    engine.register_capability(_cap())
    result = engine.execute(ExecutionRequest(_action(handler=flaky)))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert calls["n"] == 3


def test_non_retryable_failure_not_retried():
    calls = {"n": 0}

    def denied(inputs, ctx):
        calls["n"] += 1
        raise RuntimeError("permission denied")

    engine = ExecutionEngine(retry_policy=RetryPolicy(max_retries=5, backoff_seconds=0.0))
    engine.register_capability(_cap())
    result = engine.execute(ExecutionRequest(_action(handler=denied)))
    assert result.status is ExecutionStatus.FAILED
    assert calls["n"] == 1  # never retried


def test_retry_classifier():
    classifier = RetryClassifier()
    assert classifier.classify("timeout reached").retryable is True
    assert classifier.classify("permission denied").retryable is False
    assert classifier.classify("safety gate denied").retry_class is RetryClass.NON_RETRYABLE


def test_idempotent_repeat_returns_recorded_outcome():
    calls = {"n": 0}

    def side_effect(inputs, ctx):
        calls["n"] += 1
        return f"ran-{calls['n']}"

    engine = ExecutionEngine()
    engine.register_capability(_cap())
    req = ExecutionRequest(_action(handler=side_effect), inputs={"path": "x", "text": "hello"})
    first = engine.execute(req, idempotency_key="key-1")
    second = engine.execute(req, idempotency_key="key-1")
    assert first.status is ExecutionStatus.SUCCEEDED
    assert second.status is ExecutionStatus.SUCCEEDED
    assert second.reason == "idempotent replay"
    assert calls["n"] == 1  # handler ran only once


def test_approval_rejection_high_risk_goes_review():
    engine = ExecutionEngine()
    engine.register_capability(_cap())
    result = engine.execute(ExecutionRequest(_action(risk=0.8), approved=False))
    assert result.status is ExecutionStatus.REVIEW


def test_approved_high_risk_executes():
    engine = ExecutionEngine()
    engine.register_capability(_cap())
    high_risk = _action(risk=0.8, handler=lambda i, c: "ok")
    result = engine.execute(ExecutionRequest(high_risk, approved=True))
    assert result.status is ExecutionStatus.SUCCEEDED


def test_dry_run_never_invokes_handler():
    calls = {"n": 0}

    def side_effect(inputs, ctx):
        calls["n"] += 1
        return "real"

    engine = ExecutionEngine(dry_run=DryRunMode(enabled=True))
    engine.register_capability(_cap())
    result = engine.execute(ExecutionRequest(_action(handler=side_effect)))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.result["dry_run"] is True
    assert calls["n"] == 0  # handler not invoked


def test_safety_engine_deny_threshold():
    from aura_execution.safety.safety_engine import SafetyEngine

    engine = SafetyEngine()
    assert engine.evaluate(_action(risk=0.5)).decision == "ALLOW"
    assert engine.evaluate(_action(risk=0.8)).decision == "REVIEW"
    assert engine.evaluate(_action(risk=0.98)).decision == "DENY"