"""Core tests: registry, lifecycle management, container, health, bootstrap, lifecycle guard."""

from __future__ import annotations

import pytest

from aura.config.settings import AuraConfig
from aura.core.bootstrap import Bootstrap, bootstrap_aura
from aura.core.container import Container
from aura.core.context import RuntimeContext
from aura.core.health import HealthAggregator, HealthReport, HealthStatus, ReadinessStatus
from aura.core.lifecycle_manager import LifecycleManager
from aura.core.registry import ComponentRegistry
from aura.foundation.clock import FrozenClock
from aura.foundation.errors import (
    ConfigurationError,
    InvalidStateTransitionError,
    LifecycleError,
    NotFoundError,
)
from aura.foundation.lifecycle import LifecycleGuard, LifecycleState


class FakeComponent:
    """Minimal component implementing the Component protocol."""

    name = "fake"

    def __init__(self, name: str | None = None) -> None:
        if name:
            self.name = name
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def health(self) -> dict[str, object]:
        return {"status": "ok"}


def test_registry_register_get() -> None:
    registry = ComponentRegistry()
    component = FakeComponent()
    registry.register("memory", component)
    assert registry.get("memory") is component
    assert registry.has("memory")
    assert registry.names() == ["memory"]


def test_registry_duplicate_rejected() -> None:
    registry = ComponentRegistry()
    registry.register("a", FakeComponent())
    with pytest.raises(LifecycleError):
        registry.register("a", FakeComponent())


def test_registry_missing_raises() -> None:
    registry = ComponentRegistry()
    with pytest.raises(NotFoundError):
        registry.get("ghost")


def test_registry_validate_dependencies() -> None:
    registry = ComponentRegistry()
    registry.register("a", FakeComponent())
    registry.register("b", FakeComponent(), dependencies=("a",))
    assert registry.validate_graph() == []


def test_registry_detects_unknown_dependency() -> None:
    registry = ComponentRegistry()
    registry.register("a", FakeComponent(), dependencies=("ghost",))
    assert registry.validate_graph() == ["ghost"]


def test_lifecycle_manager_starts_in_dependency_order() -> None:
    registry = ComponentRegistry()
    memory = FakeComponent("memory")
    brain = FakeComponent("brain")
    registry.register("memory", memory)
    registry.register("brain", brain, dependencies=("memory",))
    lifecycle = LifecycleManager(registry)
    snapshot = lifecycle.start_all()
    assert snapshot.failed is None
    assert snapshot.started == ["memory", "brain"]
    assert memory.started and brain.started


def test_lifecycle_manager_stops_all() -> None:
    registry = ComponentRegistry()
    a = FakeComponent("a")
    registry.register("a", a)
    lifecycle = LifecycleManager(registry)
    lifecycle.start_all()
    lifecycle.stop_all()
    assert a.stopped
    assert lifecycle.is_running is False or lifecycle.snapshot().started == []


def test_container_bind_resolve() -> None:
    container = Container()
    config = AuraConfig()
    container.bind(AuraConfig, config)
    assert container.resolve(AuraConfig) is config


def test_health_aggregator_reports_healthy() -> None:
    aggregator = HealthAggregator(clock=FrozenClock())
    readiness = aggregator.readiness()
    assert readiness.status is ReadinessStatus.READY
    report = HealthReport(component="core", status=HealthStatus.OK)
    assert report.ok


def test_lifecycle_guard_legal_transition() -> None:
    guard = LifecycleGuard()
    guard.transition(LifecycleState.STARTING)
    guard.transition(LifecycleState.RUNNING)
    guard.assert_running()
    assert guard.state is LifecycleState.RUNNING


def test_lifecycle_guard_invalid_transition() -> None:
    guard = LifecycleGuard()
    with pytest.raises(InvalidStateTransitionError):
        guard.transition(LifecycleState.STOPPED)  # CREATED cannot jump to STOPPED


def test_bootstrap_start_returns_context() -> None:
    context = bootstrap_aura(clock=FrozenClock())
    assert isinstance(context, RuntimeContext)
    assert context.config is not None


def test_bootstrap_unknown_dependency_raises() -> None:
    bootstrap = Bootstrap(clock=FrozenClock())
    bootstrap.registry.register("x", FakeComponent(), dependencies=("missing",))
    with pytest.raises(ConfigurationError):
        bootstrap.start()