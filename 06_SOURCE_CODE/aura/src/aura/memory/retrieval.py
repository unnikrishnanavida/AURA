"""Retrieval scoring.

Score combines recency, importance, confidence, and keyword relevance into one
retrieval rank so recall is explainable and deterministic.

Phase 2C: relevance uses normalized token-set matching (word boundaries,
punctuation/case folding, stopword filtering) shared with the memory engine's
candidate fallback, so paraphrased queries score on shared content words rather
than on glue words or accidental substrings.
"""

from __future__ import annotations

import re
from datetime import datetime

from aura.foundation.clock import SystemClock
from aura.memory.models import MemoryEntry

#: Word-boundary tokenizer shared with the engine fallback: strips punctuation
#: so ``language.`` == ``language``.
_TOKEN_RE = re.compile(r"[a-z0-9']+")

#: Glue words excluded from relevance: they carry no topical signal and would
#: otherwise let unrelated records ("what is my favorite movie") match a
#: programming-language memory on "what/is/my/favorite" alone.
_STOPWORDS = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "do", "does", "did", "what",
        "which", "who", "whose", "whom", "my", "your", "our", "their", "his", "her",
        "i", "you", "we", "they", "of", "to", "in", "for", "on", "at", "with",
        "me", "it", "its", "this", "that", "these", "those", "about", "how",
        "favorite", "favourite", "preferred", "prefer", "prefers", "like", "likes",
        "liked", "loves", "loved", "love", "best", "good", "great", "one", "thing",
        "stuff", "code", "coding", "program", "programming", "usually",
    }
)


def meaningful_tokens(text: str) -> frozenset[str]:
    """Normalized topical tokens of ``text`` (lowercased, stopword-filtered)."""
    return frozenset(t for t in _TOKEN_RE.findall(text.lower()) if t and t not in _STOPWORDS)


def token_overlap(query_tokens: frozenset[str], haystack_tokens: frozenset[str]) -> float:
    """Fraction of query tokens present in the haystack (0.0 when empty)."""
    if not query_tokens:
        return 0.0
    return len(query_tokens & haystack_tokens) / len(query_tokens)


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
        # Phase 2C fix: token-set overlap on normalized topical tokens instead
        # of raw substring matching (``token in haystack`` let "is" match
        # inside "this" and let stopwords dominate the score).
        query_tokens = meaningful_tokens(query)
        if not query_tokens:
            # Empty/meaningless query: neutral, never decisive.
            return 0.5 if not query.strip() else 0.0
        haystack = (
            f"{entry.key} "
            + " ".join(str(v) for v in entry.content.values())
            + " "
            + " ".join(entry.tags)
        )
        return float(token_overlap(query_tokens, meaningful_tokens(haystack)))


__all__ = ["RetrievalScorer", "meaningful_tokens", "token_overlap"]