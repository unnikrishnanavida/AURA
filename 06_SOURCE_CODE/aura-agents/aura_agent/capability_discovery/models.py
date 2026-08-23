"""Capability domain models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import AgentId

__all__ = ["Capability", "CapabilityMatch", "MatchStatus"]


class MatchStatus(enum.Enum):
    """Outcome of a capability match request."""

    MATCH = "match"
    DENY = "deny"
    PARTIAL = "partial"


@dataclass(frozen=True)
class Capability:
    """A capability an agent or tool can perform.

    Capability names use dot-namespacing: ``filesystem.write``,
    ``database.read``. Matching is exact and deterministic.
    """

    name: str
    description: str = ""
    version: str = "1.0.0"
    owner_agent: AgentId | None = None
    available: bool = True
    scopes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name or "." not in self.name:
            raise ValueError(
                f"capability name must be dot-namespaced and non-empty: {self.name!r}"
            )

    def satisfies(self, required: str) -> bool:
        """True when this capability covers ``required``.

        ``required`` may end with ``.*`` to express a family of capabilities;
        a registered capability matches a wildcard request, or matches a
        concrete request exactly.
        """
        if self.name == required:
            return True
        if required.endswith(".*"):
            prefix = required[:-2]
            return self.name.startswith(prefix + ".") or self.name == prefix
        return False


@dataclass(frozen=True)
class CapabilityMatch:
    """Deterministic result of matching a required capability."""

    required: str
    status: MatchStatus
    matched: Capability | None = None
    reason: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
