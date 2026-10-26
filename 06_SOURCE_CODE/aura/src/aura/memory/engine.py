"""Memory engine.

The composed public memory API: remember, recall, forget, link, consolidate,
and replay ingestion. Uses injected store/clock/graph so memory is never a
hidden global.
"""

from __future__ import annotations

import functools
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, TypeVar, cast

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.errors import NotFoundError
from aura.foundation.ids import ExecutionId, MemoryId
from aura.memory.consolidation import Consolidator, ForgettingPolicy
from aura.memory.graph import MemoryGraph
from aura.memory.models import (
    LinkKind,
    MemoryConfidence,
    MemoryEntry,
    MemoryType,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from aura.memory.retrieval import RetrievalScorer, meaningful_tokens
from aura.memory.store import InMemoryMemoryStore, MemoryStore
from aura.observability.metrics import Metrics

F = TypeVar("F", bound=Callable[..., Any])


def _meaningful_tokens(text: str) -> list[str]:
    # Phase 2C: single canonical tokenizer lives in aura.memory.retrieval;
    # this wrapper keeps the engine's existing call sites stable.
    return sorted(meaningful_tokens(text))


def _flatten_content(entry: MemoryEntry) -> str:
    return " ".join(str(v) for v in entry.content.values())


@dataclass
class MemoryQuery:
    text: str = ""
    kind: MemoryType | None = None
    tags: tuple[str, ...] = ()
    scope: str | None = None
    limit: int = 10


class FlightRecorderLike(Protocol):
    def events(self, **filters: Any) -> list[Any]: ...


def _count_store_failure(method: F) -> F:
    """Increment ``memory_operation_failure`` exactly once on a genuine store failure.

    The canonical memory operation failure boundary: a real exception escaping a
    store-backed memory operation increments the metric (when a Metrics registry
    is wired in) and is re-raised unchanged. Two non-failure exceptions are
    never counted and simply propagate so callers keep today's control flow:

    - ``NotFoundError`` — the store contract's normal "not found" signal.
    - ``ValueError`` — caller-side validation (e.g. an out-of-range importance)
      rejected before the operation reaches persistence.

    Any other exception (OSError, backend connectivity errors, serialization
    failures, ...) is a genuine memory operation failure and must be counted
    exactly once.

    Re-entrancy: some operations compose other decorated operations (e.g.
    :meth:`MemoryEngine.archive` calls :meth:`MemoryEngine.by_id`), so one
    exception would otherwise be counted twice as it bubbles through each
    decorated boundary. A per-thread re-entrancy depth makes the increment fire
    only for the outermost failing operation boundary — one real event, one
    increment — while concurrent failures on other threads are still counted
    independently.
    """

    @functools.wraps(method)
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        _guard.depth += 1
        try:
            return method(self, *args, **kwargs)
        except (NotFoundError, ValueError):
            raise
        except Exception:
            # The outermost decorated boundary that observes this exception is
            # the one that counts it. Inner composed boundaries (e.g. by_id
            # inside archive) have depth > 1 here and must remain silent so a
            # single event never produces multiple increments.
            if _guard.depth == 1:
                metrics = getattr(self, "_metrics", None)
                if metrics is not None:
                    metrics.increment("memory_operation_failure")
            raise
        finally:
            _guard.depth -= 1

    return cast(F, wrapped)


class _FailureGuardState(threading.local):
    """Per-thread re-entrancy depth for :data:`_guard`."""

    def __init__(self) -> None:
        self.depth = 0


_guard = _FailureGuardState()


class MemoryEngine:
    def __init__(
        self,
        *,
        store: MemoryStore | None = None,
        graph: MemoryGraph | None = None,
        clock: Clock | None = None,
        scorer: RetrievalScorer | None = None,
        consolidator: Consolidator | None = None,
        forgetting: ForgettingPolicy | None = None,
        metrics: Metrics | None = None,
    ) -> None:
        self.store = store or InMemoryMemoryStore()
        self.graph = graph or MemoryGraph()
        self._clock = clock or SystemClock()
        self._scorer = scorer or RetrievalScorer()
        self._consolidator = consolidator or Consolidator()
        self._forgetting = forgetting or ForgettingPolicy()
        self._metrics = metrics

    # -- write -------------------------------------------------------------
    @_count_store_failure
    def remember(
        self,
        *,
        key: str,
        kind: MemoryType,
        content: dict[str, Any],
        importance: float = 0.5,
        confidence: MemoryConfidence | None = None,
        provenance: Provenance | None = None,
        tags: tuple[str, ...] = (),
        scope: str | None = None,
        expires_at: datetime | None = None,
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        observed_at: datetime | None = None,
        retention: RetentionPolicy | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry.create(
            key=key,
            kind=kind,
            content=content,
            importance=importance,
            confidence=confidence,
            provenance=provenance,
            clock=self._clock,
            expires_at=expires_at,
            tags=tags,
            scope=scope,
            sensitivity=sensitivity,
            observed_at=observed_at,
            retention=retention,
        )
        self.store.add(entry)
        self.graph.register(entry)
        return entry

    @_count_store_failure
    def get(self, memory_id: MemoryId) -> MemoryEntry:
        entry = self.store.get(memory_id)
        entry.touch(self._clock)
        return entry

    @_count_store_failure
    def forget(self, memory_id: MemoryId) -> None:
        self.store.delete(memory_id)

    @_count_store_failure
    def archive(self, memory_id: MemoryId) -> MemoryEntry:
        """Move a live record into the archive (retention), switching status."""
        from aura.memory.models import MemoryStatus

        entry = self.by_id(memory_id)
        if entry.status is not MemoryStatus.ACTIVE:
            raise ValueError(f"only ACTIVE records can be archived, got {entry.status.value}")
        self.store.archive(entry)
        return entry

    @_count_store_failure
    def restore(self, memory_id: MemoryId) -> MemoryEntry:
        """Restore an archived record back into the live store."""
        return self.store.restore(memory_id)

    @_count_store_failure
    def link(self, source: MemoryId, target: MemoryId, kind: LinkKind) -> None:
        from_entry = self.store.get(source)
        to_entry = self.store.get(target)
        from_entry.links[str(target)] = kind
        to_entry.links[str(source)] = kind
        self.graph.link(from_entry, to_entry, kind)

    # -- read ---------------------------------------------------------------
    @_count_store_failure
    def recall(self, query: MemoryQuery) -> list[MemoryEntry]:
        if query.scope is not None and not query.scope.strip():
            raise ValueError("memory scope must be a non-empty string when provided")
        candidates = self.store.search(
            text=query.text, kind=query.kind, tags=query.tags, scope=query.scope
        )
        if not candidates:
            # Exact-substring miss: fall back to deterministic token overlap so a
            # paraphrase ("what programming language do I prefer") can still find
            # a memory ("Python is my preferred language") without weakening the
            # scope/kind/tags filter or the bounded ranking that follows.
            candidates = self._token_overlap_candidates(
                query.text, kind=query.kind, tags=query.tags, scope=query.scope
            )
        return self._rank_and_touch(candidates, query)

    def _token_overlap_candidates(
        self,
        text: str,
        *,
        kind: Any,
        tags: tuple[str, ...],
        scope: str | None,
    ) -> list[MemoryEntry]:
        tokens = set(_meaningful_tokens(text))
        if not tokens:
            return []
        pool = self.store.search(text="", kind=kind, tags=tags, scope=scope)
        out: list[MemoryEntry] = []
        for entry in pool:
            haystack = f"{entry.key} {_flatten_content(entry)}"
            if tokens & set(_meaningful_tokens(haystack)):
                out.append(entry)
        return out

    def _rank_and_touch(self, candidates: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        ranked = sorted(
            candidates,
            key=lambda e: self._scorer.score(e, query.text, now=self._clock.now()),
            reverse=True,
        )
        for entry in ranked[: query.limit]:
            entry.touch(self._clock)
        return ranked[: query.limit]

    @_count_store_failure
    def recall_any(self, query: MemoryQuery, *, terms: tuple[str, ...] = ()) -> list[MemoryEntry]:
        """Recall entries matching the query text **or** any of ``terms``.

        :meth:`recall` is an exact-substring filter over the whole query, which
        is the right primitive for an exact lookup but returns nothing for a
        natural-language question ("when does the deployment window open?" is
        not a substring of any record). This method unions the store's index
        over the individual terms, then applies the same ranking and
        ``last_access`` handling as :meth:`recall`.

        It widens *retrieval* only: it never widens access. Callers still apply
        scope, sensitivity policy and any context budget themselves.
        """
        probes = (query.text, *terms)
        seen: dict[MemoryId, MemoryEntry] = {}
        for probe in probes:
            cleaned = probe.strip()
            if not cleaned:
                continue
            for entry in self.store.search(
                text=cleaned, kind=query.kind, tags=query.tags, scope=query.scope
            ):
                seen[entry.id] = entry
        if not seen and query.text.strip():
            # No exact/term hit: deterministic token-overlap fallback (same scope
            # filters) so paraphrased queries still recall the relevant memory.
            for entry in self._token_overlap_candidates(
                query.text, kind=query.kind, tags=query.tags, scope=query.scope
            ):
                seen[entry.id] = entry
        ranked = sorted(
            seen.values(),
            key=lambda e: self._scorer.score(e, query.text, now=self._clock.now()),
            reverse=True,
        )
        for entry in ranked[: query.limit]:
            entry.touch(self._clock)
        return ranked[: query.limit]

    @_count_store_failure
    def by_id(self, memory_id: MemoryId) -> MemoryEntry:
        return self.store.get(memory_id)

    @_count_store_failure
    def recent(self, *, kind: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        entries = [e for e in self.store.all() if kind is None or e.kind is kind]
        entries.sort(key=lambda e: e.last_access, reverse=True)
        return entries[:limit]

    # -- maintenance ----------------------------------------------------------
    @_count_store_failure
    def consolidate(self) -> list[MemoryEntry]:
        summaries = self._consolidator.consolidate(list(self.store.all()))
        for summary in summaries:
            self.store.add(summary)
            self.graph.register(summary)
        return summaries

    @_count_store_failure
    def enforce_forgetting(self) -> list[MemoryId]:
        removed: list[MemoryId] = []
        for entry in list(self.store.all()):
            if self._forgetting.eligible(entry, self._clock.now()):
                removed.append(entry.id)
                self.store.delete(entry.id)
        return removed

    @_count_store_failure
    def ingest_execution(self, recorder: FlightRecorderLike, execution_id: ExecutionId) -> list[MemoryEntry]:
        from aura.memory.replay import ReplayToMemory

        return ReplayToMemory(self.store, clock=self._clock).ingest_execution(recorder, execution_id)  # type: ignore[arg-type]

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "entries": self.store.count(),
            "backend": type(self.store).__name__,
        }


__all__ = ["MemoryEngine", "MemoryQuery"]