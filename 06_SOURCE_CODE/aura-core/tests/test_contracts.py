"""Behavioral tests for aura-core architectural contracts.

Covers: instance-scoped service registry (no hidden global state), health and
readiness checks, cancellation + timeouts, correlation context, idempotency,
DI, and event bus.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from context.correlation import CorrelationContext, new_correlation_id
from concurrency.cancellation import CancellationToken, Cancelled, TimeoutResult, TimeoutGuard
from health.contracts import HealthRegistry
from protocols.idempotency import DuplicateKeyError, IdempotencyStore, IdempotentExecutor
from registry.service_registry import ServiceRegistry


def test_service_registry_instance_scoped_no_global_state():
    """Registries must not share hidden global state."""
    a, b = ServiceRegistry(), ServiceRegistry()
    a.register("db", object())
    assert a.get("db") is not None
    assert b.get("db") is None  # no shared global
    assert b.names() == ()


def test_service_registry_require_missing_raises():
    registry = ServiceRegistry()
    with pytest.raises(KeyError):
        registry.require("missing")


def test_service_registry_contains_and_clear():
    registry = ServiceRegistry()
    registry.register("svc", 42)
    assert "svc" in registry
    registry.clear()
    assert "svc" not in registry


def test_health_registry_all_healthy():
    registry = HealthRegistry()
    registry.register("kernel", lambda: (True, "running"))
    registry.register("config", lambda: (True, "loaded"))
    assert registry.healthy() is True
    results = registry.run()
    assert all(r["ok"] for r in results)


def test_health_registry_unhealthy_detected():
    registry = HealthRegistry()
    registry.register("kernel", lambda: (True, "running"))
    registry.register("db", lambda: (False, "connection refused"))
    assert registry.healthy() is False


def test_health_registry_check_exception_reports_fail():
    registry = HealthRegistry()

    def boom() -> tuple[bool, str]:
        raise RuntimeError("exploded")

    registry.register("boom", boom)
    assert registry.healthy() is False
    assert "RuntimeError" in registry.run()[0]["detail"]


def test_cancellation_token_fails_closed():
    token = CancellationToken()
    assert token.cancelled is False
    token.cancel()
    with pytest.raises(Cancelled):
        token.check()


def test_timeout_guard_reports_elapsed():
    guard = TimeoutGuard(timeout_seconds=10.0)
    import time

    elapsed, value = guard.run(lambda: time.sleep(0.001) or 7)
    assert value == 7
    assert guard.exceeded(elapsed) is False


def test_timeout_result_shape():
    result = TimeoutResult(ok=False, elapsed=5.0)
    assert result.timed_out is True


def test_correlation_context_carries_id():
    ctx = CorrelationContext()
    assert ctx.correlation_id.startswith("co-")
    assert len(ctx.correlation_id) > 0
    child = ctx.child()
    assert child.correlation_id == ctx.correlation_id  # same logical trace


def test_new_correlation_id_unique():
    assert new_correlation_id() != new_correlation_id()


def test_idempotency_store_rejects_duplicate_key():
    store = IdempotencyStore()
    store.set("k", {"ok": True})
    with pytest.raises(DuplicateKeyError):
        store.set("k", {"ok": False})


def test_idempotent_executor_replays():
    calls = {"n": 0}

    def run() -> dict:
        calls["n"] += 1
        return {"n": calls["n"]}

    executor = IdempotentExecutor()
    first = executor.execute("key", run)
    second = executor.execute("key", run)
    assert first.replayed is False
    assert second.replayed is True
    assert second.outcome == first.outcome
    assert calls["n"] == 1  # fn ran once


def test_injector_singleton_and_transient():
    from dependency_injection.injector import Injector

    injector = Injector()
    injector.register("singleton", lambda: object())
    injector.register("transient", lambda: object(), singleton=False)
    assert injector.get("singleton") is injector.get("singleton")
    assert injector.get("transient") is not injector.get("transient")


def test_event_bus_publish_subscribe():
    from events.event_bus import EventBus
    from events.event import Event

    received = []

    def _handler(event: Event) -> None:
        received.append(event.payload)

    bus = EventBus()
    bus.subscribe("topic", _handler)
    bus.publish(Event(name="topic", payload={"value": 1}))
    assert received == [{"value": 1}]