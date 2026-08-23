"""Agent identity domain.

``AgentId`` is defined in :mod:`aura_agent.contracts.ids` (the canonical ID
type); this module provides the richer identity record and the registry that
owns it. No second ID type is created.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.ids import AgentId

__all__ = ["AgentIdentity", "AgentVersion", "IdentityRegistry"]


@dataclass(frozen=True)
class AgentVersion:
    """Version metadata for an agent."""

    major: int = 0
    minor: int = 1
    patch: int = 0
    build: str = ""

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}+{self.build}" if self.build else base


@dataclass(frozen=True)
class AgentIdentity:
    """The immutable identity of an agent instance."""

    agent_id: AgentId
    name: str
    version: AgentVersion = field(default_factory=AgentVersion)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    @property
    def qualified_name(self) -> str:
        return f"{self.name}@{self.version}"


class IdentityRegistry:
    """Maps agent ids to their identities."""

    def __init__(self) -> None:
        self._identities: dict[AgentId, AgentIdentity] = {}

    def register(self, identity: AgentIdentity) -> None:
        self._identities[identity.agent_id] = identity

    def get(self, agent_id: AgentId) -> AgentIdentity:
        if agent_id not in self._identities:
            raise KeyError(f"unknown agent {agent_id}")
        return self._identities[agent_id]

    def all(self) -> list[AgentIdentity]:
        return list(self._identities.values())

    def has(self, agent_id: AgentId) -> bool:
        return agent_id in self._identities