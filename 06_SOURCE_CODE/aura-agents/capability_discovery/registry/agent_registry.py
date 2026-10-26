"""Agent <-> capability index for discovery and delegation.

Note: this file intentionally consolidates the scaffold's
``registry/agent_registry.py`` and ``registry/availability_registry.py`` into a
single ownership: who can do what, and whether they are currently available.
Availability is a first-class field, matching the registry semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_agent.contracts.ids import AgentId

__all__ = ["AgentCapabilityRegistry", "AgentCapabilityEntry"]


@dataclass(frozen=True)
class AgentCapabilityEntry:
    """A single agent's known capabilities and availability."""

    agent_id: AgentId
    capabilities: frozenset[str]
    available: bool = True
    version: str = "1.0.0"


class AgentCapabilityRegistry:
    """Maps agents to their exposed capabilities.

    Used by the discovery engine and by delegation/multi-agent selection to
    answer "which agents can satisfy capability X".
    """

    def __init__(self) -> None:
        self._entries: dict[AgentId, AgentCapabilityEntry] = {}

    def register(
        self,
        agent_id: AgentId,
        capabilities: set[str] | frozenset[str] | list[str],
        *,
        available: bool = True,
        version: str = "1.0.0",
    ) -> None:
        self._entries[agent_id] = AgentCapabilityEntry(
            agent_id=agent_id,
            capabilities=frozenset(capabilities),
            available=available,
            version=version,
        )

    def set_available(self, agent_id: AgentId, available: bool) -> None:
        entry = self._entries.get(agent_id)
        if entry is not None:
            self._entries[agent_id] = AgentCapabilityEntry(
                agent_id=agent_id,
                capabilities=entry.capabilities,
                available=available,
                version=entry.version,
            )

    def matching_agents(self, required: str) -> list[AgentCapabilityEntry]:
        """All available agents whose capability set satisfies ``required``."""
        prefix = required[:-2] if required.endswith(".*") else None
        result: list[AgentCapabilityEntry] = []
        for entry in self._entries.values():
            if not entry.available:
                continue
            for cap in entry.capabilities:
                if cap == required or (prefix is not None and (cap == prefix or cap.startswith(prefix + "."))):
                    result.append(entry)
                    break
        return sorted(result, key=lambda e: e.agent_id)

    def agents(self) -> list[AgentCapabilityEntry]:
        return list(self._entries.values())
