"""Bootstrap.

Bootstrap is the single entry point that:
1. loads and validates configuration,
2. builds the shared primitives (clock, registries, container, health),
3. performs dependency validation across all registered components,
4. provisions the runtime context.

Domain engines register themselves; the :class:`LifecycleManager` starts them
in dependency order.
"""

from __future__ import annotations

from aura.config.settings import AuraConfig
from aura.core.container import Container
from aura.core.context import RuntimeContext
from aura.core.health import HealthAggregator
from aura.core.lifecycle_manager import LifecycleManager
from aura.core.registry import ComponentRegistry
from aura.foundation.clock import Clock, SystemClock
from aura.foundation.errors import ConfigurationError


class Bootstrap:
    """Bootstraps the AURA runtime from validated settings."""

    def __init__(self, config: AuraConfig | None = None, clock: Clock | None = None) -> None:
        self.config = config or AuraConfig()
        self.clock = clock or SystemClock()
        self.registry = ComponentRegistry()
        self.container = Container()
        self.health = HealthAggregator(clock=self.clock)
        self.lifecycle = LifecycleManager(self.registry)

    def wire_core(self) -> Bootstrap:
        """Register the foundational services in the container and health bus."""
        self.container.bind(AuraConfig, self.config)
        self.container.bind(Clock, self.clock)
        self.container.bind(ComponentRegistry, self.registry)
        self.container.bind(HealthAggregator, self.health)
        return self

    def validate(self) -> Bootstrap:
        unknown = self.registry.validate_graph()
        if unknown:
            raise ConfigurationError(f"components depend on unknown components: {unknown}")
        return self

    def context(self, *, name: str = "aura") -> RuntimeContext:
        return RuntimeContext(
            config=self.config,
            clock=self.clock,
            registry=self.registry,
            container=self.container,
            health=self.health,
            name=name,
        )

    def start(self) -> RuntimeContext:
        """Wire core, validate dependencies, and start all registered components."""
        self.wire_core().validate()
        snapshot = self.lifecycle.start_all()
        if snapshot.failed is not None:
            raise ConfigurationError(
                f"component {snapshot.failed!r} failed to start: {snapshot.reason}"
            )
        return self.context()

    def shutdown(self) -> None:
        self.lifecycle.stop_all()


def bootstrap_aura(
    *,
    config: AuraConfig | None = None,
    clock: Clock | None = None,
    name: str = "aura",
) -> RuntimeContext:
    """Convenience entry point: build, validate, and start the runtime."""
    return Bootstrap(config=config, clock=clock).start()


__all__ = ["Bootstrap", "bootstrap_aura"]