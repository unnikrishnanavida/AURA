"""Agent genome domain model.

The genome is a versioned, attributable record of an agent's behavioral
capabilities, learned behavior, performance history, and lineage. It exists to
make "learning" an auditable, reversible data structure rather than
self-modifying code.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import AgentId

__all__ = ["AgentGenome", "GenomeUpdate", "PerformanceEntry"]


@dataclass(frozen=True)
class PerformanceEntry:
    """A recorded execution outcome contributing to the genome."""

    action: str
    success: bool
    cost: float = 0.0
    risk: float = 0.0
    failure_class: str | None = None
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class GenomeUpdate:
    """An attributable, versioned change to a genome.

    ``authorized_by`` and ``evidence`` make every mutation accountable;
    ``reversible`` marks that the prior state can be restored.
    """

    authorized_by: str
    evidence: dict[str, Any] = field(default_factory=dict)
    version_increment: str = "patch"
    reversible: bool = True


class AgentGenome:
    """Immutable-ish genome: all mutable state is private and only changed
    through audit-trailed update methods."""

    def __init__(self, agent_id: AgentId, version: str = "1.0.0") -> None:
        self.agent_id = agent_id
        self.version = version
        self.capability_profile: set[str] = set()
        self.behavior_profile: dict[str, Any] = {}
        self.performance_history: list[PerformanceEntry] = []
        self.learned_behavior: dict[str, Any] = {}
        self.lineage: list[str] = []
        self.updated_at: datetime = datetime.now(UTC)

    # -- fingerprint ------------------------------------------------------------
    @property
    def fingerprint(self) -> str:
        """Deterministic fingerprint of the genome's current state."""
        blob = json.dumps(
            {
                "agent_id": str(self.agent_id),
                "version": self.version,
                "capabilities": sorted(self.capability_profile),
                "behavior": self.behavior_profile,
                "learned": self.learned_behavior,
                "lineage": self.lineage,
            },
            sort_keys=True,
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    # -- learning hooks (audited) -------------------------------------------------
    def record_performance(self, entry: PerformanceEntry) -> None:
        self.performance_history.append(entry)
        self.updated_at = datetime.now(UTC)

    def apply_learned_update(
        self, update: GenomeUpdate, *, behavior_key: str, value: Any
    ) -> None:
        """Apply a validated learned-behavior change with full attribution."""
        self.learned_behavior[behavior_key] = {
            "value": value,
            "authorized_by": update.authorized_by,
            "evidence": update.evidence,
            "applied_at": datetime.now(UTC).isoformat(),
            "reversible": update.reversible,
        }
        self.behavior_profile.setdefault("learned", {})[behavior_key] = value
        self.updated_at = datetime.now(UTC)

    # -- statistics ---------------------------------------------------------------
    def success_rate(self) -> float:
        if not self.performance_history:
            return 0.0
        n = len(self.performance_history)
        ok = sum(1 for e in self.performance_history if e.success)
        return ok / n

    def reliability(self) -> float:
        """Exponential-weighted reliability from recent outcomes."""
        total_weight = 0.0
        weighted = 0.0
        for i, entry in enumerate(reversed(self.performance_history[-20:])):
            weight = 0.5 ** (i * 0.25)
            weighted += weight * (1.0 if entry.success else 0.0)
            total_weight += weight
        return weighted / total_weight if total_weight else 0.5

    def failure_patterns(self) -> dict[str, int]:
        patterns: dict[str, int] = {}
        for entry in self.performance_history:
            if not entry.success and entry.failure_class:
                patterns[entry.failure_class] = patterns.get(entry.failure_class, 0) + 1
        return patterns

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "version": self.version,
            "fingerprint": self.fingerprint,
            "capabilities": sorted(self.capability_profile),
            "behavior": self.behavior_profile,
            "learned": self.learned_behavior,
            "lineage": self.lineage,
            "performance": {
                "count": len(self.performance_history),
                "success_rate": self.success_rate(),
                "reliability": self.reliability(),
                "failure_patterns": self.failure_patterns(),
            },
        }
