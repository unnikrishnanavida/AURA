"""Capability discovery engine.

Answers two questions:

1. Can *this* agent perform capability ``X``?
   (delegated to the capability registry's deterministic matcher)
2. Which *other* agents are available and capable of ``X``?
   (delegated to the agent-capability index)

The engine deliberately contains **no matching logic of its own**; it composes
the registry and the index so there is exactly one matching algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_agent.capability_discovery.models import CapabilityMatch
from aura_agent.capability_discovery.registry.agent_registry import (
    AgentCapabilityEntry,
    AgentCapabilityRegistry,
)
from aura_agent.capability_discovery.registry.capability_registry import (
    CapabilityRegistry,
)
from aura_agent.contracts.ids import AgentId

__all__ = ["DiscoveryEngine", "DiscoveryResult"]


@dataclass(frozen=True)
class DiscoveryResult:
    """Cumulative discovery answer."""

    self_match: CapabilityMatch
    agents: list[tuple[AgentId, str]]


class DiscoveryEngine:
    """Composes local capability matching with remote agent discovery."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        agent_registry: AgentCapabilityRegistry | None = None,
    ) -> None:
        self._capabilities = capability_registry
        self._agents = agent_registry or AgentCapabilityRegistry()

    @property
    def agent_registry(self) -> AgentCapabilityRegistry:
        return self._agents

    def discover(
        self, required: str, *, scopes: list[str] | None = None
    ) -> DiscoveryResult:
        """Discover agents capable of ``required``.

        The local capability registry is authoritative for *self*; the agent
        index is authoritative for *other* agents. Both use the same matching
        semantics (exact or ``.*`` wildcard).
        """
        local = self._capabilities.match(required, scopes=scopes)
        others: list[tuple[AgentId, str]] = []
        for entry in self._agents.matching_agents(required):
            others.append((entry.agent_id, entry.version))
        return DiscoveryResult(self_match=local, agents=others)