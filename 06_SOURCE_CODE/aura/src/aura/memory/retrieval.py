"""Retrieval scoring.

Score combines recency, importance, confidence, and keyword relevance into one
retrieval rank so recall is explainable and deterministic.
"""

from __future__ import annotations

from datetime import datetime

from aura.foundation.clock import SystemClock
from aura.memory.models import MemoryEntry


class RetrievalScorer:
    """Produces a [0,1] relevance score for a memory entry against a query."""

    recency_half_life_seconds: float = 3600.0

    def score(self, entry: MemoryEntry, query: str = "", *, now: datetime | None = None) -> float:
        now = now or SystemClock().now()
        recency = self._recency(entry, now)
        importance = entry.importance
        confidence = entry.confidence.combined
        relevance = self._relevance(entry, query)
        return 0.25 * importance + 0.25 * confidence + 0.3 * relevance + 0.2 * recency

    def _recency(self, entry: MemoryEntry, now: datetime) -> float:
        age = (now - entry.last_access).total_seconds()
        if self.recency_half_life_seconds <= 0:
            return 0.0
        return float(round(0.5 ** (age / self.recency_half_life_seconds), 6))

    @staticmethod
    def _relevance(entry: MemoryEntry, query: str) -> float:
        needle = query.strip().lower()
        if not needle:
            return 0.5
        haystack = (
            f"{entry.key} ".lower()
            + " ".join(str(v).lower() for v in entry.content.values())
            + " "
            + " ".join(entry.tags)
        )
        tokens = [t for t in needle.split() if t]
        if not tokens:
            return 0.0
        hits = sum(1 for token in tokens if token in haystack)
        return float(min(1.0, hits / len(tokens)))


__all__ = ["RetrievalScorer"]