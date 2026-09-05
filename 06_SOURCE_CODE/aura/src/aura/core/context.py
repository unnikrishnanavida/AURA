"""Runtime context.

Every engine receives a :class:`RuntimeContext` through dependency injection.
It carries cross-cutting state (configuration, clock, correlation id,
execution id, registries) without leaking global singleton state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.config.settings import AuraConfig
from aura.core.container import Container
from aura.core.health import HealthAggregator
from aura.core.registry import ComponentRegistry
from aura.foundation.clock import Clock
from aura.foundation.ids import CorrelationId, ExecutionId


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    config: AuraConfig
    clock: Clock
    registry: ComponentRegistry
    container: Container
    health: HealthAggregator
    name: str = "aura"
    correlation_id: CorrelationId = field(default_factory=CorrelationId.new)
    execution_id: ExecutionId = field(default_factory=ExecutionId.new)

    def child(self, *, name: str | None = None) -> RuntimeContext:
        """Derive a child context for a unit of work that carries a fresh correlation."""
        return RuntimeContext(
            config=self.config,
            clock=self.clock,
            registry=self.registry,
            container=self.container,
            health=self.health,
            name=name if name is not None else self.name,
            correlation_id=CorrelationId.new(),
            execution_id=self.execution_id,
        )

    def component(self, name: str) -> object | None:
        return self.registry.get(name) if self.registry.has(name) else None


__all__ = ["RuntimeContext"]