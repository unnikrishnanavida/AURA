"""Consolidation and forgetting.

Consolidator turns clusters of episodic memories into semantic summaries.
ForgettingPolicy removes expired entries and passively decays the importance
of rarely accessed memories.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime

from aura.foundation.clock import Clock, SystemClock
from aura.memory.models import MemoryEntry, MemoryType, Provenance


class ForgettingPolicy:
    def __init__(self, *, decay_per_access: float = 0.05, importance_floor: float = 0.1) -> None:
        self.decay_per_access = decay_per_access
        self.importance_floor = importance_floor

    def eligible(self, entry: MemoryEntry, now: datetime | None = None) -> bool:
        now = now or SystemClock().now()
        if entry.expired(now):
            return True
        return entry.importance < self.importance_floor


class Consolidator:
    """Merges episodic memories into a semantic summary.

    Honest about its limits: consolidation only summarizes, it does not invent
    relationships that were not present in the source episodes.
    """

    def __init__(self, *, min_episodes: int = 2, clock: Clock | None = None) -> None:
        self.min_episodes = min_episodes
        self._clock = clock or SystemClock()

    def consolidate(self, episodes: Iterable[MemoryEntry]) -> list[MemoryEntry]:
        buckets: dict[str, list[MemoryEntry]] = defaultdict(list)
        for episode in episodes:
            if episode.kind is not MemoryType.EPISODIC:
                continue
            topic = episode.key.split(":")[0] if ":" in episode.key else episode.key
            buckets[topic].append(episode)

        summaries: list[MemoryEntry] = []
        for topic, group in buckets.items():
            if len(group) < self.min_episodes:
                continue
            combined = {
                "topic": topic,
                "episodes": [str(e.id) for e in group],
                "occurrences": len(group),
                "observed": [e.content for e in group if e.content],
            }
            avg_confidence = sum(e.confidence.combined for e in group) / len(group)
            avg_importance = sum(e.importance for e in group) / len(group)
            summaries.append(
                MemoryEntry.create(
                    key=f"semantic:{topic}",
                    kind=MemoryType.SEMANTIC,
                    content=combined,
                    importance=min(1.0, avg_importance + 0.1),
                    confidence=type(group[0].confidence)(
                        fact=avg_confidence,
                        source=avg_confidence,
                        freshness=max(e.confidence.freshness for e in group),
                    ),
                    provenance=Provenance(source="consolidation", creator="consolidator"),
                    clock=self._clock,
                )
            )
        return summaries


__all__ = ["Consolidator", "ForgettingPolicy"]