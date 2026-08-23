"""
AURA Foundation - Memory Cache.

High-performance in-process memory cache built on top of the core cache
contracts. This module is intentionally focused on process-local storage,
memory accounting, eviction behavior, lifecycle management, bulk access,
statistics, warming, and operational inspection.

The implementation is designed to work with the sibling ``cache.py`` module
without requiring the rest of the AURA foundation to be initialized first.

Major capabilities:

* O(1)-average key lookup through an ordered dictionary
* LRU, FIFO, LFU, MRU, and size-aware eviction policies
* TTL and stale-value support
* configurable entry and byte limits
* per-entry metadata
* tags and tag invalidation
* atomic add/replace/delete operations
* compare-and-set versions
* single-flight value computation
* bulk get/set/delete operations
* memory usage estimation
* admission filtering
* hit/miss/eviction statistics
* event listeners
* cache snapshots
* warmup and preloading
* namespace views
* freeze/unfreeze lifecycle
* health and diagnostics
* synchronous and asynchronous helpers
* cache decorators
* maintenance and compaction operations

This is a storage-specialized cache. Persistent disk concerns belong in
``disk_cache.py`` and policy composition belongs in ``policy.py``.
"""

from __future__ import annotations

import asyncio
import copy
import functools
import hashlib
import inspect
import pickle
import threading
import time
from collections import OrderedDict, defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, ParamSpec, TypeVar

try:
    from .cache import (
        Cache,
        CacheClosedError,
        CacheConfigurationError,
        CacheEntry,
        CacheError,
        CacheEvent,
        CacheEventType,
        CacheFrozenError,
        CacheLockTimeout,
        CacheSnapshot,
        CacheStats,
        CacheVersionError,
        EvictionReason,
        estimate_size,
        hash_key,
        normalize_key,
        normalize_namespace,
    )
except ImportError:
    # This fallback keeps the module importable in isolated development.
    class CacheError(Exception):
        pass

    class CacheClosedError(CacheError):
        pass

    class CacheConfigurationError(CacheError, ValueError):
        pass

    class CacheFrozenError(CacheError):
        pass

    class CacheLockTimeout(CacheError, TimeoutError):
        pass

    class CacheVersionError(CacheError):
        pass

    class CacheEventType(StrEnum):
        GET = "get"
        HIT = "hit"
        MISS = "miss"
        SET = "set"
        ADD = "add"
        REPLACE = "replace"
        DELETE = "delete"
        EVICT = "evict"
        EXPIRE = "expire"
        CLEAR = "clear"
        INVALIDATE = "invalidate"
        ERROR = "error"
        RESTORE = "restore"

    class EvictionReason(StrEnum):
        CAPACITY = "capacity"
        EXPIRED = "expired"
        EXPLICIT = "explicit"
        INVALIDATED = "invalidated"
        CLEAR = "clear"
        REPLACED = "replaced"

    def normalize_namespace(namespace: str | None) -> str:
        return str(namespace or "default").strip() or "default"

    def normalize_key(
        key: Any,
        *,
        namespace: str | None = None,
    ) -> str:
        value = str(key).strip()
        if not value:
            raise ValueError("empty cache key")
        return f"{normalize_namespace(namespace)}:{value}"

    def hash_key(key: Any) -> str:
        return hashlib.sha256(
            str(key).encode()
        ).hexdigest()

    def estimate_size(value: Any) -> int:
        try:
            return len(
                pickle.dumps(
                    value,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            )
        except Exception:
            return max(1, len(repr(value)))

    @dataclass
    class CacheEntry:
        key: str
        value: Any
        created_at: float
        expires_at: float | None = None
        accessed_at: float = 0.0
        access_count: int = 0
        size: int = 0
        version: int = 1
        tags: frozenset[str] = frozenset()
        stale: bool = False
        negative: bool = False

        def is_expired(self, now: float | None = None) -> bool:
            if self.expires_at is None:
                return False
            return (
                self.expires_at
                <= (
                    time.monotonic()
                    if now is None
                    else now
                )
            )

        def remaining_ttl(
            self,
            now: float | None = None,
        ) -> float | None:
            if self.expires_at is None:
                return None
            return max(
                0.0,
                self.expires_at
                - (
                    time.monotonic()
                    if now is None
                    else now
                ),
            )

        def clone(self):
            return copy.copy(self)

    @dataclass(frozen=True)
    class CacheEvent:
        event_type: CacheEventType
        key: str | None
        timestamp: float
        namespace: str
        value: Any = None
        reason: EvictionReason | None = None
        metadata: Mapping[str, Any] = field(
            default_factory=dict
        )

    @dataclass
    class CacheStats:
        hits: int = 0
        misses: int = 0
        sets: int = 0
        adds: int = 0
        replaces: int = 0
        deletes: int = 0
        evictions: int = 0
        expirations: int = 0
        invalidations: int = 0
        clears: int = 0
        errors: int = 0

        @property
        def requests(self):
            return self.hits + self.misses

        @property
        def hit_rate(self):
            return (
                self.hits / self.requests
                if self.requests
                else 0.0
            )

        def snapshot(self):
            return dict(self.__dict__)

    @dataclass(frozen=True)
    class CacheSnapshot:
        namespace: str
        created_at: float
        entries: tuple
        stats: Mapping[str, Any]


P = ParamSpec("P")
T = TypeVar("T")
V = TypeVar("V")


# ============================================================================
# Constants
# ============================================================================

DEFAULT_MEMORY_MAX_ENTRIES = 10_000
DEFAULT_MEMORY_MAX_BYTES = 0
DEFAULT_MEMORY_TTL = 3600.0
DEFAULT_SAMPLE_SIZE = 32
DEFAULT_COMPACTION_INTERVAL = 256
DEFAULT_LOCK_TIMEOUT = 30.0
DEFAULT_MEMORY_NAMESPACE = "memory"


# ============================================================================
# Exceptions
# ============================================================================

class MemoryCacheError(CacheError):
    """Base exception for memory-cache-specific failures."""


class MemoryCapacityError(MemoryCacheError):
    """Raised when a value cannot fit into configured memory capacity."""


class MemoryPolicyError(MemoryCacheError):
    """Raised when an invalid memory eviction policy is selected."""


class MemorySnapshotError(MemoryCacheError):
    """Raised when a memory-cache snapshot is invalid."""


# ============================================================================
# Enums
# ============================================================================

class MemoryEvictionPolicy(StrEnum):
    """Supported in-memory eviction policies."""

    LRU = "lru"
    FIFO = "fifo"
    LFU = "lfu"
    MRU = "mru"
    SMALLEST = "smallest"
    LARGEST = "largest"


class MemoryEntryState(StrEnum):
    """Operational state of a memory entry."""

    ACTIVE = "active"
    STALE = "stale"
    EXPIRED = "expired"


# ============================================================================
# Records
# ============================================================================

@dataclass
class MemoryCacheConfig:
    """Validated configuration for MemoryCache."""

    namespace: str = DEFAULT_MEMORY_NAMESPACE
    default_ttl: float | None = DEFAULT_MEMORY_TTL
    max_entries: int = DEFAULT_MEMORY_MAX_ENTRIES
    max_bytes: int = DEFAULT_MEMORY_MAX_BYTES
    eviction_policy: MemoryEvictionPolicy = (
        MemoryEvictionPolicy.LRU
    )
    allow_stale: bool = False
    stale_grace: float = 0.0
    copy_values: bool = False
    sample_size: int = DEFAULT_SAMPLE_SIZE
    compaction_interval: int = DEFAULT_COMPACTION_INTERVAL
    lock_timeout: float = DEFAULT_LOCK_TIMEOUT

    def validate(self) -> None:
        if self.default_ttl is not None and self.default_ttl < 0:
            raise CacheConfigurationError(
                "default_ttl cannot be negative"
            )

        if self.max_entries < 0:
            raise CacheConfigurationError(
                "max_entries cannot be negative"
            )

        if self.max_bytes < 0:
            raise CacheConfigurationError(
                "max_bytes cannot be negative"
            )

        if self.stale_grace < 0:
            raise CacheConfigurationError(
                "stale_grace cannot be negative"
            )

        if self.sample_size <= 0:
            raise CacheConfigurationError(
                "sample_size must be positive"
            )

        if self.compaction_interval <= 0:
            raise CacheConfigurationError(
                "compaction_interval must be positive"
            )

        if self.lock_timeout < 0:
            raise CacheConfigurationError(
                "lock_timeout cannot be negative"
            )


@dataclass
class MemoryEntry(CacheEntry[V], Generic[V]):
    """Memory-cache entry with additional storage metadata."""

    weight: float = 1.0
    insertion_sequence: int = 0
    last_refresh_at: float = 0.0
    generation: int = 0
    protected: bool = False

    def state(
        self,
        now: float,
        *,
        stale_grace: float = 0.0,
    ) -> MemoryEntryState:
        if self.expires_at is None:
            return MemoryEntryState.ACTIVE

        if now < self.expires_at:
            return MemoryEntryState.ACTIVE

        if (
            stale_grace > 0
            and now
            <= self.expires_at + stale_grace
        ):
            return MemoryEntryState.STALE

        return MemoryEntryState.EXPIRED

    def clone(self) -> "MemoryEntry[V]":
        return MemoryEntry(
            key=self.key,
            value=self.value,
            created_at=self.created_at,
            expires_at=self.expires_at,
            accessed_at=self.accessed_at,
            access_count=self.access_count,
            size=self.size,
            version=self.version,
            tags=frozenset(self.tags),
            stale=self.stale,
            negative=self.negative,
            weight=self.weight,
            insertion_sequence=self.insertion_sequence,
            last_refresh_at=self.last_refresh_at,
            generation=self.generation,
            protected=self.protected,
        )


@dataclass
class MemoryStats(CacheStats):
    """Extended statistics for memory caching."""

    stale_hits: int = 0
    protected_hits: int = 0
    refreshes: int = 0
    capacity_evictions: int = 0
    policy_evictions: int = 0
    rejected_entries: int = 0
    compactions: int = 0
    bytes_evicted: int = 0
    peak_entries: int = 0
    peak_bytes: int = 0
    maintenance_runs: int = 0
    maintenance_removed: int = 0
    warmup_entries: int = 0
    failed_warmups: int = 0
    compute_calls: int = 0
    compute_waits: int = 0

    def snapshot(self) -> dict[str, Any]:
        result = dict(self.__dict__)
        result["requests"] = self.requests
        result["hit_rate"] = self.hit_rate
        result["miss_rate"] = (
            self.misses / self.requests
            if self.requests
            else 0.0
        )
        return result


@dataclass(frozen=True)
class MemorySnapshot:
    """Immutable snapshot specialized for MemoryCache."""

    namespace: str
    created_at: float
    entries: tuple[MemoryEntry[Any], ...]
    stats: Mapping[str, Any]
    policy: str
    max_entries: int
    max_bytes: int

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def byte_count(self) -> int:
        return sum(
            entry.size
            for entry in self.entries
        )


@dataclass(frozen=True)
class MemoryCacheInfo:
    """Operational summary of a memory cache."""

    namespace: str
    state: str
    entries: int
    bytes: int
    max_entries: int
    max_bytes: int
    policy: str
    hit_rate: float
    stale_entries: int
    expired_entries: int
    protected_entries: int
    tags: int


# ============================================================================
# Eviction helpers
# ============================================================================

def _entry_lru_key(
    entry: MemoryEntry[Any],
) -> tuple[float, int]:
    return (
        entry.accessed_at,
        entry.insertion_sequence,
    )


def _entry_fifo_key(
    entry: MemoryEntry[Any],
) -> int:
    return entry.insertion_sequence


def _entry_lfu_key(
    entry: MemoryEntry[Any],
) -> tuple[int, float, int]:
    return (
        entry.access_count,
        entry.accessed_at,
        entry.insertion_sequence,
    )


def _entry_mru_key(
    entry: MemoryEntry[Any],
) -> tuple[float, int]:
    return (
        -entry.accessed_at,
        -entry.insertion_sequence,
    )


def _entry_size_key(
    entry: MemoryEntry[Any],
) -> tuple[int, int]:
    return (
        entry.size,
        entry.insertion_sequence,
    )


def _entry_large_key(
    entry: MemoryEntry[Any],
) -> tuple[int, int]:
    return (
        -entry.size,
        entry.insertion_sequence,
    )


# ============================================================================
# MemoryCache
# ============================================================================

class MemoryCache(Cache[V], Generic[V]):
    """High-performance process-local memory cache.

    The class intentionally owns its storage instead of relying on an
    external mapping. This makes capacity enforcement and eviction
    deterministic and keeps the implementation suitable for AURA's
    foundation layer.
    """

    def __init__(
        self,
        *,
        namespace: str = DEFAULT_MEMORY_NAMESPACE,
        default_ttl: float | None = DEFAULT_MEMORY_TTL,
        max_entries: int = DEFAULT_MEMORY_MAX_ENTRIES,
        max_bytes: int = DEFAULT_MEMORY_MAX_BYTES,
        eviction_policy: (
            MemoryEvictionPolicy | str
        ) = MemoryEvictionPolicy.LRU,
        allow_stale: bool = False,
        stale_grace: float = 0.0,
        copy_values: bool = False,
        sample_size: int = DEFAULT_SAMPLE_SIZE,
        compaction_interval: int = DEFAULT_COMPACTION_INTERVAL,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.memory_config = MemoryCacheConfig(
            namespace=normalize_namespace(namespace),
            default_ttl=default_ttl,
            max_entries=max_entries,
            max_bytes=max_bytes,
            eviction_policy=self._normalize_policy(
                eviction_policy
            ),
            allow_stale=allow_stale,
            stale_grace=stale_grace,
            copy_values=copy_values,
            sample_size=sample_size,
            compaction_interval=compaction_interval,
            lock_timeout=lock_timeout,
        )
        self.memory_config.validate()

        self._clock = clock
        self._entries: OrderedDict[
            str,
            MemoryEntry[V],
        ] = OrderedDict()

        self._tags: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        self._lock = threading.RLock()
        self._fill_locks: dict[
            str,
            threading.Lock,
        ] = {}

        self._listeners: list[
            Callable[[CacheEvent], None]
        ] = []

        self._stats = MemoryStats()
        self._state = "ready"
        self._total_bytes = 0
        self._sequence = 0
        self._operations = 0
        self._generation = 0

    # ------------------------------------------------------------------
    # Configuration and lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_policy(
        policy: MemoryEvictionPolicy | str,
    ) -> MemoryEvictionPolicy:
        if isinstance(
            policy,
            MemoryEvictionPolicy,
        ):
            return policy

        try:
            return MemoryEvictionPolicy(
                str(policy).strip().lower()
            )
        except ValueError as exc:
            raise MemoryPolicyError(
                f"Unknown memory eviction policy: {policy!r}"
            ) from exc

    @property
    def namespace(self) -> str:
        return self.memory_config.namespace

    @property
    def config(self) -> MemoryCacheConfig:
        return self.memory_config

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def stats(self) -> MemoryStats:
        return self._stats

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def total_size(self) -> int:
        return self.total_bytes

    @property
    def total_bytes(self) -> int:
        with self._lock:
            return self._total_bytes

    @property
    def max_entries(self) -> int:
        return self.memory_config.max_entries

    @property
    def max_bytes(self) -> int:
        return self.memory_config.max_bytes

    @property
    def eviction_policy(self) -> MemoryEvictionPolicy:
        return self.memory_config.eviction_policy

    def initialize(self) -> None:
        with self._lock:
            if self._state == "closed":
                raise CacheClosedError(
                    "Cannot initialize a closed memory cache."
                )
            self._state = "ready"

    def close(self) -> None:
        with self._lock:
            if self._state == "closed":
                return

            self._entries.clear()
            self._tags.clear()
            self._fill_locks.clear()
            self._total_bytes = 0
            self._state = "closed"

    def shutdown(self) -> None:
        self.close()

    def freeze(self) -> None:
        with self._lock:
            self._ensure_open()
            self._state = "frozen"

    def unfreeze(self) -> None:
        with self._lock:
            self._ensure_open()
            self._state = "ready"

    def reset(self) -> None:
        self._ensure_mutable()
        self.clear()
        self.reset_stats()

    def _ensure_open(self) -> None:
        if self._state == "closed":
            raise CacheClosedError(
                "Memory cache is closed."
            )

    def _ensure_mutable(self) -> None:
        self._ensure_open()
        if self._state == "frozen":
            raise CacheFrozenError(
                "Memory cache is frozen."
            )

    # ------------------------------------------------------------------
    # Key and time helpers
    # ------------------------------------------------------------------

    def _now(self) -> float:
        return float(self._clock())

    def key(
        self,
        key: Any,
    ) -> str:
        return normalize_key(
            key,
            namespace=self.namespace,
        )

    def key_hash(
        self,
        key: Any,
    ) -> str:
        return hash_key(
            self.key(key)
        )

    def _expires_at(
        self,
        ttl: float | None,
    ) -> float | None:
        selected = (
            self.memory_config.default_ttl
            if ttl is None
            else ttl
        )

        if selected is None:
            return None

        if selected < 0:
            raise CacheConfigurationError(
                "TTL cannot be negative."
            )

        return self._now() + selected

    def _copy_in(
        self,
        value: V,
    ) -> V:
        if not self.memory_config.copy_values:
            return value

        try:
            return copy.deepcopy(value)
        except Exception:
            try:
                return pickle.loads(
                    pickle.dumps(
                        value,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )
                )
            except Exception:
                return value

    def _copy_out(
        self,
        value: V,
    ) -> V:
        return self._copy_in(value)

    def _measure(
        self,
        value: Any,
    ) -> int:
        return max(
            1,
            estimate_size(value),
        )

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def _next_generation(self) -> int:
        self._generation += 1
        return self._generation

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def add_listener(
        self,
        listener: Callable[[CacheEvent], None],
    ) -> None:
        if not callable(listener):
            raise TypeError(
                "listener must be callable"
            )

        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(
                    listener
                )

    def remove_listener(
        self,
        listener: Callable[[CacheEvent], None],
    ) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(
                    listener
                )

    def _emit(
        self,
        event_type: CacheEventType,
        *,
        key: str | None = None,
        value: Any = None,
        reason: EvictionReason | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        event = CacheEvent(
            event_type=event_type,
            key=key,
            timestamp=time.time(),
            namespace=self.namespace,
            value=None,
            reason=reason,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            listeners = tuple(
                self._listeners
            )

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                self._stats.errors += 1

    # ------------------------------------------------------------------
    # Entry state
    # ------------------------------------------------------------------

    def _entry_state(
        self,
        entry: MemoryEntry[V],
        now: float | None = None,
    ) -> MemoryEntryState:
        return entry.state(
            self._now()
            if now is None
            else now,
            stale_grace=self.memory_config.stale_grace,
        )

    def _is_readable(
        self,
        entry: MemoryEntry[V],
        now: float | None = None,
        *,
        allow_stale: bool | None = None,
    ) -> bool:
        current = (
            self._now()
            if now is None
            else now
        )

        state = self._entry_state(
            entry,
            current,
        )

        if state == MemoryEntryState.ACTIVE:
            return True

        if state == MemoryEntryState.STALE:
            return (
                self.memory_config.allow_stale
                if allow_stale is None
                else allow_stale
            )

        return False

    def _mark_stale_if_needed(
        self,
        entry: MemoryEntry[V],
        now: float,
    ) -> None:
        if (
            entry.expires_at is not None
            and now >= entry.expires_at
        ):
            entry.stale = True

    # ------------------------------------------------------------------
    # Storage bookkeeping
    # ------------------------------------------------------------------

    def _attach_tags(
        self,
        entry: MemoryEntry[V],
    ) -> None:
        for tag in entry.tags:
            self._tags[tag].add(
                entry.key
            )

    def _detach_tags(
        self,
        entry: MemoryEntry[V],
    ) -> None:
        for tag in entry.tags:
            keys = self._tags.get(tag)
            if keys is None:
                continue

            keys.discard(entry.key)

            if not keys:
                self._tags.pop(
                    tag,
                    None,
                )

    def _remove_entry_locked(
        self,
        key: str,
        *,
        reason: EvictionReason,
        count_eviction: bool = True,
    ) -> MemoryEntry[V] | None:
        entry = self._entries.pop(
            key,
            None,
        )

        if entry is None:
            return None

        self._detach_tags(entry)
        self._total_bytes = max(
            0,
            self._total_bytes - entry.size,
        )

        if reason == EvictionReason.EXPLICIT:
            self._stats.deletes += 1

        elif reason == EvictionReason.EXPIRED:
            self._stats.expirations += 1

        elif reason == EvictionReason.INVALIDATED:
            self._stats.invalidations += 1

        elif (
            reason == EvictionReason.CAPACITY
            and count_eviction
        ):
            self._stats.evictions += 1
            self._stats.capacity_evictions += 1
            self._stats.policy_evictions += 1
            self._stats.bytes_evicted += entry.size

        if reason in (
            EvictionReason.CAPACITY,
            EvictionReason.EXPIRED,
            EvictionReason.INVALIDATED,
        ):
            self._emit(
                (
                    CacheEventType.EXPIRE
                    if reason == EvictionReason.EXPIRED
                    else CacheEventType.EVICT
                ),
                key=key,
                reason=reason,
                metadata={
                    "size": entry.size,
                    "version": entry.version,
                    "policy": (
                        self.eviction_policy.value
                    ),
                },
            )

        return entry

    def _delete_expired_locked(
        self,
        *,
        limit: int | None = None,
    ) -> int:
        now = self._now()
        removed = 0

        for key, entry in tuple(
            self._entries.items()
        ):
            if (
                limit is not None
                and removed >= limit
            ):
                break

            if self._entry_state(
                entry,
                now,
            ) != MemoryEntryState.EXPIRED:
                continue

            if self._remove_entry_locked(
                key,
                reason=EvictionReason.EXPIRED,
            ) is not None:
                removed += 1

        return removed

    def _record_peak_locked(self) -> None:
        self._stats.peak_entries = max(
            self._stats.peak_entries,
            len(self._entries),
        )
        self._stats.peak_bytes = max(
            self._stats.peak_bytes,
            self._total_bytes,
        )

    # ------------------------------------------------------------------
    # Eviction selection
    # ------------------------------------------------------------------

    def _candidate_entries_locked(
        self,
    ) -> list[MemoryEntry[V]]:
        return [
            entry
            for entry in self._entries.values()
            if not entry.protected
        ]

    def _select_eviction_candidate_locked(
        self,
    ) -> MemoryEntry[V] | None:
        candidates = self._candidate_entries_locked()

        if not candidates:
            return None

        policy = self.eviction_policy

        if policy == MemoryEvictionPolicy.LRU:
            return min(
                candidates,
                key=_entry_lru_key,
            )

        if policy == MemoryEvictionPolicy.FIFO:
            return min(
                candidates,
                key=_entry_fifo_key,
            )

        if policy == MemoryEvictionPolicy.LFU:
            return min(
                candidates,
                key=_entry_lfu_key,
            )

        if policy == MemoryEvictionPolicy.MRU:
            return min(
                candidates,
                key=_entry_mru_key,
            )

        if policy == MemoryEvictionPolicy.SMALLEST:
            return min(
                candidates,
                key=_entry_size_key,
            )

        if policy == MemoryEvictionPolicy.LARGEST:
            return min(
                candidates,
                key=_entry_large_key,
            )

        raise MemoryPolicyError(
            f"Unsupported eviction policy: {policy}"
        )

    def _over_capacity_locked(self) -> bool:
        if (
            self.max_entries > 0
            and len(self._entries)
            > self.max_entries
        ):
            return True

        if (
            self.max_bytes > 0
            and self._total_bytes
            > self.max_bytes
        ):
            return True

        return False

    def _evict_until_fit_locked(self) -> int:
        removed = 0

        while self._over_capacity_locked():
            candidate = (
                self._select_eviction_candidate_locked()
            )

            if candidate is None:
                raise MemoryCapacityError(
                    "All memory-cache entries are protected; "
                    "capacity cannot be satisfied."
                )

            removed_entry = (
                self._remove_entry_locked(
                    candidate.key,
                    reason=EvictionReason.CAPACITY,
                )
            )

            if removed_entry is None:
                break

            removed += 1

        return removed

    # ------------------------------------------------------------------
    # Core read operations
    # ------------------------------------------------------------------

    def get(
        self,
        key: Any,
        default: Any = None,
        *,
        allow_stale: bool | None = None,
    ) -> Any:
        self._ensure_open()
        normalized = self.key(key)

        with self._lock:
            self._stats.requests += 0
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                self._stats.misses += 1
                self._emit(
                    CacheEventType.MISS,
                    key=normalized,
                )
                return default

            now = self._now()
            state = self._entry_state(
                entry,
                now,
            )

            if state == MemoryEntryState.EXPIRED:
                self._remove_entry_locked(
                    normalized,
                    reason=EvictionReason.EXPIRED,
                )
                self._stats.misses += 1
                self._emit(
                    CacheEventType.MISS,
                    key=normalized,
                )
                return default

            if state == MemoryEntryState.STALE:
                permitted = (
                    self.memory_config.allow_stale
                    if allow_stale is None
                    else allow_stale
                )

                if not permitted:
                    self._stats.misses += 1
                    self._emit(
                        CacheEventType.MISS,
                        key=normalized,
                        metadata={
                            "reason": "stale",
                        },
                    )
                    return default

                entry.stale = True
                self._stats.stale_hits += 1

            entry.access_count += 1
            entry.accessed_at = now
            self._entries.move_to_end(
                normalized
            )

            self._stats.hits += 1

            if entry.protected:
                self._stats.protected_hits += 1

            self._emit(
                CacheEventType.HIT,
                key=normalized,
                metadata={
                    "stale": entry.stale,
                    "version": entry.version,
                    "access_count": entry.access_count,
                },
            )

            return self._copy_out(
                entry.value
            )

    def peek(
        self,
        key: Any,
        default: Any = None,
        *,
        allow_stale: bool = False,
    ) -> Any:
        self._ensure_open()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return default

            if not self._is_readable(
                entry,
                self._now(),
                allow_stale=allow_stale,
            ):
                return default

            return self._copy_out(
                entry.value
            )

    def contains(
        self,
        key: Any,
        *,
        allow_stale: bool = False,
    ) -> bool:
        sentinel = object()
        return (
            self.get(
                key,
                sentinel,
                allow_stale=allow_stale,
            )
            is not sentinel
        )

    def exists(
        self,
        key: Any,
    ) -> bool:
        return self.contains(key)

    def require(
        self,
        key: Any,
    ) -> V:
        sentinel = object()
        value = self.get(
            key,
            sentinel,
        )

        if value is sentinel:
            raise KeyError(
                self.key(key)
            )

        return value

    # ------------------------------------------------------------------
    # Core write operations
    # ------------------------------------------------------------------

    def set(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        version: int | None = None,
        weight: float = 1.0,
        protected: bool = False,
        negative: bool = False,
    ) -> V:
        self._ensure_mutable()

        normalized = self.key(key)

        if weight <= 0:
            raise CacheConfigurationError(
                "weight must be positive"
            )

        prepared = self._copy_in(
            value
        )
        size = self._measure(
            prepared
        )
        now = self._now()

        tag_set = frozenset(
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        )

        with self._lock:
            previous = self._entries.get(
                normalized
            )

            if version is None:
                version = (
                    previous.version + 1
                    if previous is not None
                    else 1
                )

            if previous is not None:
                self._detach_tags(
                    previous
                )
                self._total_bytes = max(
                    0,
                    self._total_bytes
                    - previous.size,
                )

            entry = MemoryEntry(
                key=normalized,
                value=prepared,
                created_at=now,
                expires_at=(
                    None
                    if ttl is None
                    and self.memory_config.default_ttl is None
                    else (
                        self._expires_at(ttl)
                    )
                ),
                accessed_at=now,
                access_count=0,
                size=size,
                version=version,
                tags=tag_set,
                stale=False,
                negative=negative,
                weight=float(weight),
                insertion_sequence=self._next_sequence(),
                last_refresh_at=now,
                generation=self._next_generation(),
                protected=protected,
            )

            self._entries[
                normalized
            ] = entry
            self._entries.move_to_end(
                normalized
            )
            self._total_bytes += size

            self._attach_tags(
                entry
            )

            self._stats.sets += 1
            self._stats.bytes_written = (
                getattr(
                    self._stats,
                    "bytes_written",
                    0,
                )
                + size
            )

            if previous is not None:
                self._stats.refreshes += 1

            self._record_peak_locked()
            self._operations += 1

            if (
                self._operations
                % self.memory_config.compaction_interval
                == 0
            ):
                self._maintenance_locked(
                    max_items=self.memory_config.sample_size
                )

            try:
                self._evict_until_fit_locked()
            except Exception:
                self._entries.pop(
                    normalized,
                    None,
                )
                self._detach_tags(
                    entry
                )
                self._total_bytes = max(
                    0,
                    self._total_bytes
                    - entry.size,
                )
                if previous is not None:
                    self._entries[
                        normalized
                    ] = previous
                    self._attach_tags(
                        previous
                    )
                    self._total_bytes += previous.size
                raise

        self._emit(
            CacheEventType.SET,
            key=normalized,
            metadata={
                "size": size,
                "version": version,
                "ttl": (
                    None
                    if entry.expires_at is None
                    else max(
                        0.0,
                        entry.expires_at
                        - now,
                    )
                ),
                "protected": protected,
            },
        )

        return self._copy_out(
            prepared
        )

    def add(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        weight: float = 1.0,
        protected: bool = False,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is not None:
                if self._entry_state(
                    entry
                ) == MemoryEntryState.EXPIRED:
                    self._remove_entry_locked(
                        normalized,
                        reason=EvictionReason.EXPIRED,
                    )
                else:
                    return False

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
            weight=weight,
            protected=protected,
        )

        with self._lock:
            self._stats.adds += 1

        self._emit(
            CacheEventType.ADD,
            key=normalized,
        )

        return True

    def replace(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        weight: float = 1.0,
        protected: bool = False,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            if (
                self._entry_state(entry)
                == MemoryEntryState.EXPIRED
            ):
                self._remove_entry_locked(
                    normalized,
                    reason=EvictionReason.EXPIRED,
                )
                return False

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
            weight=weight,
            protected=protected,
        )

        with self._lock:
            self._stats.replaces += 1

        self._emit(
            CacheEventType.REPLACE,
            key=normalized,
        )

        return True

    def setdefault(
        self,
        key: Any,
        default: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
    ) -> V:
        sentinel = object()
        value = self.get(
            key,
            sentinel,
        )

        if value is not sentinel:
            return value

        self.set(
            key,
            default,
            ttl=ttl,
            tags=tags,
        )

        return default

    # ------------------------------------------------------------------
    # Delete operations
    # ------------------------------------------------------------------

    def delete(
        self,
        key: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._remove_entry_locked(
                normalized,
                reason=EvictionReason.EXPLICIT,
            )

        if entry is None:
            return False

        self._emit(
            CacheEventType.DELETE,
            key=normalized,
        )

        return True

    def pop(
        self,
        key: Any,
        default: Any = None,
    ) -> Any:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._remove_entry_locked(
                normalized,
                reason=EvictionReason.EXPLICIT,
            )

        if entry is None:
            return default

        self._emit(
            CacheEventType.DELETE,
            key=normalized,
        )

        return self._copy_out(
            entry.value
        )

    def delete_many(
        self,
        keys: Iterable[Any],
    ) -> int:
        count = 0

        for key in keys:
            if self.delete(key):
                count += 1

        return count

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def get_many(
        self,
        keys: Iterable[Any],
        *,
        include_missing: bool = False,
        allow_stale: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        sentinel = object()

        for key in keys:
            normalized = self.key(key)
            value = self.get(
                normalized,
                sentinel,
                allow_stale=allow_stale,
            )

            if (
                value is not sentinel
                or include_missing
            ):
                result[normalized] = (
                    None
                    if value is sentinel
                    else value
                )

        return result

    def set_many(
        self,
        values: Mapping[Any, V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
    ) -> int:
        count = 0

        for key, value in values.items():
            self.set(
                key,
                value,
                ttl=ttl,
                tags=tags,
            )
            count += 1

        return count

    def add_many(
        self,
        values: Mapping[Any, V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
    ) -> int:
        count = 0

        for key, value in values.items():
            if self.add(
                key,
                value,
                ttl=ttl,
                tags=tags,
            ):
                count += 1

        return count

    def contains_many(
        self,
        keys: Iterable[Any],
    ) -> dict[str, bool]:
        return {
            self.key(key): self.contains(key)
            for key in keys
        }

    # ------------------------------------------------------------------
    # TTL and expiration
    # ------------------------------------------------------------------

    def ttl(
        self,
        key: Any,
    ) -> float | None:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return None

            if entry.expires_at is None:
                return None

            return max(
                0.0,
                entry.expires_at
                - self._now(),
            )

    def expire(
        self,
        key: Any,
        ttl: float,
    ) -> bool:
        self._ensure_mutable()

        if ttl < 0:
            raise CacheConfigurationError(
                "TTL cannot be negative"
            )

        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.expires_at = (
                self._now() + ttl
            )
            entry.stale = False
            entry.last_refresh_at = self._now()

            return True

    def persist(
        self,
        key: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.expires_at = None
            entry.stale = False
            entry.last_refresh_at = self._now()

            return True

    def refresh_ttl(
        self,
        key: Any,
        ttl: float | None = None,
    ) -> bool:
        selected = (
            self.memory_config.default_ttl
            if ttl is None
            else ttl
        )

        if selected is None:
            return self.persist(key)

        return self.expire(
            key,
            selected,
        )

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    def version(
        self,
        key: Any,
    ) -> int | None:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return None

            if (
                self._entry_state(entry)
                == MemoryEntryState.EXPIRED
            ):
                return None

            return entry.version

    def get_with_version(
        self,
        key: Any,
    ) -> tuple[Any, int | None]:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                self._stats.misses += 1
                return None, None

            if not self._is_readable(
                entry
            ):
                return None, None

            entry.access_count += 1
            entry.accessed_at = self._now()
            self._entries.move_to_end(
                normalized
            )
            self._stats.hits += 1

            return (
                self._copy_out(entry.value),
                entry.version,
            )

    def compare_and_set(
        self,
        key: Any,
        expected_version: int | None,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        protected: bool = False,
    ) -> int:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            current = (
                None
                if entry is None
                else entry.version
            )

            if current != expected_version:
                raise CacheVersionError(
                    f"Version mismatch for {normalized!r}: "
                    f"expected={expected_version!r}, "
                    f"actual={current!r}"
                )

            new_version = (
                1
                if entry is None
                else entry.version + 1
            )

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
            version=new_version,
            protected=protected,
        )

        return new_version

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tags(self) -> list[str]:
        with self._lock:
            return sorted(
                self._tags.keys()
            )

    def keys_for_tag(
        self,
        tag: str,
    ) -> list[str]:
        normalized = str(tag).strip()

        with self._lock:
            return sorted(
                self._tags.get(
                    normalized,
                    set(),
                )
            )

    def tags_for_key(
        self,
        key: Any,
    ) -> set[str]:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return set()

            return set(
                entry.tags
            )

    def invalidate_tag(
        self,
        tag: str,
    ) -> int:
        self._ensure_mutable()
        normalized = str(tag).strip()

        with self._lock:
            keys = tuple(
                self._tags.get(
                    normalized,
                    set(),
                )
            )

        count = 0

        for key in keys:
            if self.delete(key):
                count += 1

        if count:
            with self._lock:
                self._stats.invalidations += count

            self._emit(
                CacheEventType.INVALIDATE,
                metadata={
                    "tag": normalized,
                    "count": count,
                },
            )

        return count

    def invalidate_prefix(
        self,
        prefix: str,
    ) -> int:
        self._ensure_mutable()
        text = str(prefix)

        with self._lock:
            keys = [
                key
                for key in self._entries
                if key.startswith(text)
            ]

        return self.delete_many(
            keys
        )

    # ------------------------------------------------------------------
    # Protected entries
    # ------------------------------------------------------------------

    def protect(
        self,
        key: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.protected = True
            return True

    def unprotect(
        self,
        key: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.protected = False
            return True

    def is_protected(
        self,
        key: Any,
    ) -> bool:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            return bool(
                entry is not None
                and entry.protected
            )

    # ------------------------------------------------------------------
    # Compute / single-flight
    # ------------------------------------------------------------------

    def _fill_lock_for(
        self,
        normalized: str,
    ) -> threading.Lock:
        with self._lock:
            lock = self._fill_locks.get(
                normalized
            )

            if lock is None:
                lock = threading.Lock()
                self._fill_locks[
                    normalized
                ] = lock

            return lock

    def get_or_set(
        self,
        key: Any,
        factory: Callable[[], V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        protected: bool = False,
    ) -> V:
        if not callable(factory):
            raise TypeError(
                "factory must be callable"
            )

        sentinel = object()
        value = self.get(
            key,
            sentinel,
        )

        if value is not sentinel:
            return value

        normalized = self.key(key)
        lock = self._fill_lock_for(
            normalized
        )

        acquired = lock.acquire(
            timeout=self.memory_config.lock_timeout
        )

        if not acquired:
            raise CacheLockTimeout(
                f"Timed out filling {normalized!r}"
            )

        try:
            value = self.get(
                normalized,
                sentinel,
            )

            if value is not sentinel:
                with self._lock:
                    self._stats.compute_waits += 1
                return value

            with self._lock:
                self._stats.compute_calls += 1

            result = factory()

            self.set(
                normalized,
                result,
                ttl=ttl,
                tags=tags,
                protected=protected,
            )

            return result
        finally:
            lock.release()

    async def aget_or_set(
        self,
        key: Any,
        factory: Callable[[], Any],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        protected: bool = False,
    ) -> Any:
        sentinel = object()
        value = self.get(
            key,
            sentinel,
        )

        if value is not sentinel:
            return value

        normalized = self.key(key)
        lock = self._fill_lock_for(
            normalized
        )

        acquired = await asyncio.to_thread(
            lock.acquire,
            True,
            self.memory_config.lock_timeout,
        )

        if not acquired:
            raise CacheLockTimeout(
                f"Timed out filling {normalized!r}"
            )

        try:
            value = self.get(
                normalized,
                sentinel,
            )

            if value is not sentinel:
                with self._lock:
                    self._stats.compute_waits += 1
                return value

            with self._lock:
                self._stats.compute_calls += 1

            result = factory()

            if inspect.isawaitable(result):
                result = await result

            self.set(
                normalized,
                result,
                ttl=ttl,
                tags=tags,
                protected=protected,
            )

            return result
        finally:
            lock.release()

    # ------------------------------------------------------------------
    # Cleanup and maintenance
    # ------------------------------------------------------------------

    def cleanup_expired(
        self,
        *,
        limit: int | None = None,
    ) -> int:
        self._ensure_mutable()

        with self._lock:
            removed = self._delete_expired_locked(
                limit=limit
            )
            self._stats.maintenance_runs += 1
            self._stats.maintenance_removed += removed

        return removed

    def _maintenance_locked(
        self,
        *,
        max_items: int | None = None,
    ) -> int:
        removed = self._delete_expired_locked(
            limit=max_items
        )

        self._stats.compactions += 1
        self._stats.maintenance_runs += 1
        self._stats.maintenance_removed += removed

        return removed

    def maintenance(
        self,
        *,
        max_items: int | None = None,
    ) -> dict[str, int]:
        self._ensure_mutable()

        with self._lock:
            before = len(
                self._entries
            )
            before_bytes = self._total_bytes

            expired = self._maintenance_locked(
                max_items=max_items
            )

            self._evict_until_fit_locked()

            after = len(
                self._entries
            )
            after_bytes = self._total_bytes

        return {
            "expired_removed": expired,
            "entries_before": before,
            "entries_after": after,
            "bytes_before": before_bytes,
            "bytes_after": after_bytes,
        }

    def compact(self) -> int:
        return self.cleanup_expired()

    # ------------------------------------------------------------------
    # Iteration and inspection
    # ------------------------------------------------------------------

    def keys(
        self,
        *,
        include_expired: bool = False,
    ) -> list[str]:
        self._ensure_open()

        if not include_expired:
            self.cleanup_expired()

        with self._lock:
            return list(
                self._entries.keys()
            )

    def values(
        self,
        *,
        include_expired: bool = False,
    ) -> list[V]:
        return [
            self.peek(key)
            for key in self.keys(
                include_expired=include_expired
            )
        ]

    def items(
        self,
        *,
        include_expired: bool = False,
    ) -> list[tuple[str, V]]:
        return [
            (
                key,
                self.peek(key),
            )
            for key in self.keys(
                include_expired=include_expired
            )
        ]

    def entries(
        self,
        *,
        include_expired: bool = True,
    ) -> list[MemoryEntry[V]]:
        self._ensure_open()

        if not include_expired:
            self.cleanup_expired()

        with self._lock:
            return [
                entry.clone()
                for entry in self._entries.values()
            ]

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[str]:
        return iter(
            self.keys()
        )

    def __contains__(
        self,
        key: object,
    ) -> bool:
        try:
            return self.contains(key)
        except Exception:
            return False

    def __getitem__(
        self,
        key: Any,
    ) -> Any:
        return self.require(key)

    def __setitem__(
        self,
        key: Any,
        value: Any,
    ) -> None:
        self.set(
            key,
            value,
        )

    def __repr__(self) -> str:
        return (
            "MemoryCache("
            f"namespace={self.namespace!r}, "
            f"entries={self.size}, "
            f"bytes={self.total_bytes}, "
            f"policy={self.eviction_policy.value!r}, "
            f"state={self.state!r})"
        )

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def snapshot(self) -> MemorySnapshot:
        self._ensure_open()

        with self._lock:
            entries = tuple(
                entry.clone()
                for entry in self._entries.values()
            )
            stats = self._stats.snapshot()

            return MemorySnapshot(
                namespace=self.namespace,
                created_at=time.time(),
                entries=entries,
                stats=stats,
                policy=self.eviction_policy.value,
                max_entries=self.max_entries,
                max_bytes=self.max_bytes,
            )

    def restore(
        self,
        snapshot: MemorySnapshot,
        *,
        clear_first: bool = True,
    ) -> int:
        self._ensure_mutable()

        if not isinstance(
            snapshot,
            MemorySnapshot,
        ):
            raise MemorySnapshotError(
                "Invalid memory-cache snapshot."
            )

        if snapshot.namespace != self.namespace:
            raise MemorySnapshotError(
                "Snapshot namespace does not match cache."
            )

        if clear_first:
            self.clear()

        restored = 0

        now = self._now()

        with self._lock:
            for entry in snapshot.entries:
                if (
                    self._entry_state(
                        entry,
                        now,
                    )
                    == MemoryEntryState.EXPIRED
                ):
                    continue

                clone = entry.clone()

                self._entries[
                    clone.key
                ] = clone
                self._total_bytes += clone.size
                self._attach_tags(
                    clone
                )
                restored += 1

            self._evict_until_fit_locked()

        self._emit(
            CacheEventType.RESTORE,
            metadata={
                "restored": restored,
            },
        )

        return restored

    def export_bytes(self) -> bytes:
        try:
            return pickle.dumps(
                self.snapshot(),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise MemorySnapshotError(
                "Unable to serialize memory snapshot."
            ) from exc

    def import_bytes(
        self,
        payload: bytes,
        *,
        clear_first: bool = True,
    ) -> int:
        try:
            snapshot = pickle.loads(
                payload
            )
        except Exception as exc:
            raise MemorySnapshotError(
                "Unable to deserialize memory snapshot."
            ) from exc

        return self.restore(
            snapshot,
            clear_first=clear_first,
        )

    # ------------------------------------------------------------------
    # Statistics and diagnostics
    # ------------------------------------------------------------------

    def stats_snapshot(self) -> dict[str, Any]:
        with self._lock:
            stats = self._stats.snapshot()

            stats.update({
                "namespace": self.namespace,
                "state": self._state,
                "entries": len(self._entries),
                "bytes": self._total_bytes,
                "max_entries": self.max_entries,
                "max_bytes": self.max_bytes,
                "eviction_policy": (
                    self.eviction_policy.value
                ),
                "default_ttl": (
                    self.memory_config.default_ttl
                ),
                "allow_stale": (
                    self.memory_config.allow_stale
                ),
                "stale_grace": (
                    self.memory_config.stale_grace
                ),
            })

            return stats

    def reset_stats(self) -> None:
        with self._lock:
            self._stats = MemoryStats()

    def stale_count(self) -> int:
        now = self._now()

        with self._lock:
            return sum(
                1
                for entry in self._entries.values()
                if self._entry_state(
                    entry,
                    now,
                ) == MemoryEntryState.STALE
            )

    def expired_count(self) -> int:
        now = self._now()

        with self._lock:
            return sum(
                1
                for entry in self._entries.values()
                if self._entry_state(
                    entry,
                    now,
                ) == MemoryEntryState.EXPIRED
            )

    def protected_count(self) -> int:
        with self._lock:
            return sum(
                1
                for entry in self._entries.values()
                if entry.protected
            )

    def memory_utilization(self) -> float:
        if self.max_bytes <= 0:
            return 0.0

        return min(
            1.0,
            self.total_bytes / self.max_bytes,
        )

    def entry_utilization(self) -> float:
        if self.max_entries <= 0:
            return 0.0

        return min(
            1.0,
            self.size / self.max_entries,
        )

    def info(self) -> MemoryCacheInfo:
        stats = self.stats_snapshot()

        return MemoryCacheInfo(
            namespace=self.namespace,
            state=self.state,
            entries=self.size,
            bytes=self.total_bytes,
            max_entries=self.max_entries,
            max_bytes=self.max_bytes,
            policy=self.eviction_policy.value,
            hit_rate=float(
                stats.get(
                    "hit_rate",
                    0.0,
                )
            ),
            stale_entries=self.stale_count(),
            expired_entries=self.expired_count(),
            protected_entries=self.protected_count(),
            tags=len(self.tags()),
        )

    def health(self) -> bool:
        try:
            with self._lock:
                self._ensure_open()

                if self._total_bytes < 0:
                    return False

                if len(self._entries) < 0:
                    return False

                actual = sum(
                    entry.size
                    for entry in self._entries.values()
                )

                if actual != self._total_bytes:
                    return False

                return True
        except Exception:
            return False

    def diagnose(self) -> dict[str, Any]:
        return {
            "health": self.health(),
            "info": self.info(),
            "stats": self.stats_snapshot(),
            "memory_utilization": (
                self.memory_utilization()
            ),
            "entry_utilization": (
                self.entry_utilization()
            ),
            "keys": self.keys(
                include_expired=True
            ),
        }

    # ------------------------------------------------------------------
    # Warming and bulk population
    # ------------------------------------------------------------------

    def warm(
        self,
        values: Mapping[Any, V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        protected: bool = False,
        replace: bool = True,
    ) -> int:
        loaded = 0

        for key, value in values.items():
            if (
                not replace
                and self.contains(key)
            ):
                continue

            try:
                self.set(
                    key,
                    value,
                    ttl=ttl,
                    tags=tags,
                    protected=protected,
                )
                loaded += 1
            except Exception:
                with self._lock:
                    self._stats.failed_warmups += 1

        with self._lock:
            self._stats.warmup_entries += loaded

        return loaded

    def warm_from(
        self,
        source: Mapping[Any, V] | Callable[[], Mapping[Any, V]],
        **kwargs: Any,
    ) -> int:
        values = (
            source()
            if callable(source)
            else source
        )

        return self.warm(
            values,
            **kwargs,
        )

    def preload(
        self,
        keys: Iterable[Any],
        loader: Callable[[str], V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
    ) -> int:
        count = 0

        for key in keys:
            normalized = self.key(key)

            try:
                value = loader(
                    normalized
                )
                self.set(
                    normalized,
                    value,
                    ttl=ttl,
                    tags=tags,
                )
                count += 1
            except Exception:
                with self._lock:
                    self._stats.failed_warmups += 1

        return count

    # ------------------------------------------------------------------
    # Namespace helpers
    # ------------------------------------------------------------------

    def scoped(
        self,
        namespace_name: str,
    ) -> "MemoryCacheNamespace":
        return MemoryCacheNamespace(
            self,
            namespace_name,
        )

    # ------------------------------------------------------------------
    # Capacity management
    # ------------------------------------------------------------------

    def set_limits(
        self,
        *,
        max_entries: int | None = None,
        max_bytes: int | None = None,
    ) -> int:
        self._ensure_mutable()

        if max_entries is not None and max_entries < 0:
            raise CacheConfigurationError(
                "max_entries cannot be negative"
            )

        if max_bytes is not None and max_bytes < 0:
            raise CacheConfigurationError(
                "max_bytes cannot be negative"
            )

        with self._lock:
            if max_entries is not None:
                self.memory_config.max_entries = (
                    max_entries
                )

            if max_bytes is not None:
                self.memory_config.max_bytes = (
                    max_bytes
                )

            return self._evict_until_fit_locked()

    def set_policy(
        self,
        policy: MemoryEvictionPolicy | str,
    ) -> int:
        self._ensure_mutable()
        normalized = self._normalize_policy(
            policy
        )

        with self._lock:
            self.memory_config.eviction_policy = normalized
            return self._evict_until_fit_locked()

    # ------------------------------------------------------------------
    # Weight and entry metadata
    # ------------------------------------------------------------------

    def weight(
        self,
        key: Any,
    ) -> float | None:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            return (
                None
                if entry is None
                else entry.weight
            )

    def set_weight(
        self,
        key: Any,
        weight: float,
    ) -> bool:
        self._ensure_mutable()

        if weight <= 0:
            raise CacheConfigurationError(
                "weight must be positive"
            )

        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.weight = float(weight)
            return True

    def entry_metadata(
        self,
        key: Any,
    ) -> dict[str, Any] | None:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return None

            return {
                "key": entry.key,
                "size": entry.size,
                "weight": entry.weight,
                "version": entry.version,
                "created_at": entry.created_at,
                "accessed_at": entry.accessed_at,
                "access_count": entry.access_count,
                "expires_at": entry.expires_at,
                "ttl": (
                    entry.remaining_ttl(
                        self._now()
                    )
                ),
                "tags": sorted(entry.tags),
                "stale": entry.stale,
                "protected": entry.protected,
                "generation": entry.generation,
                "insertion_sequence": (
                    entry.insertion_sequence
                ),
            }

    # ------------------------------------------------------------------
    # Sampling and policy analysis
    # ------------------------------------------------------------------

    def sample(
        self,
        count: int | None = None,
    ) -> list[MemoryEntry[V]]:
        selected = (
            self.memory_config.sample_size
            if count is None
            else count
        )

        if selected <= 0:
            return []

        with self._lock:
            entries = list(
                self._entries.values()
            )

            return [
                entry.clone()
                for entry in entries[:selected]
            ]

    def policy_preview(
        self,
        count: int = 1,
    ) -> list[str]:
        if count <= 0:
            return []

        with self._lock:
            candidates = self._candidate_entries_locked()

            policy = self.eviction_policy

            if policy == MemoryEvictionPolicy.LRU:
                ordered = sorted(
                    candidates,
                    key=_entry_lru_key,
                )
            elif policy == MemoryEvictionPolicy.FIFO:
                ordered = sorted(
                    candidates,
                    key=_entry_fifo_key,
                )
            elif policy == MemoryEvictionPolicy.LFU:
                ordered = sorted(
                    candidates,
                    key=_entry_lfu_key,
                )
            elif policy == MemoryEvictionPolicy.MRU:
                ordered = sorted(
                    candidates,
                    key=_entry_mru_key,
                )
            elif policy == MemoryEvictionPolicy.SMALLEST:
                ordered = sorted(
                    candidates,
                    key=_entry_size_key,
                )
            elif policy == MemoryEvictionPolicy.LARGEST:
                ordered = sorted(
                    candidates,
                    key=_entry_large_key,
                )
            else:
                raise MemoryPolicyError(
                    f"Unsupported policy: {policy}"
                )

            return [
                entry.key
                for entry in ordered[:count]
            ]

    # ------------------------------------------------------------------
    # Clear and context management
    # ------------------------------------------------------------------

    def clear(
        self,
        *,
        emit: bool = True,
    ) -> int:
        self._ensure_mutable()

        with self._lock:
            count = len(
                self._entries
            )

            self._entries.clear()
            self._tags.clear()
            self._total_bytes = 0
            self._stats.clears += 1

        if emit:
            self._emit(
                CacheEventType.CLEAR,
                metadata={
                    "count": count,
                },
            )

        return count

    def __enter__(
        self,
    ) -> "MemoryCache[V]":
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        self.close()


# ============================================================================
# Namespace view
# ============================================================================

class MemoryCacheNamespace(Generic[V]):
    """Scoped view over a MemoryCache."""

    def __init__(
        self,
        cache: MemoryCache[V],
        namespace: str,
    ) -> None:
        self.cache = cache
        self.namespace = normalize_namespace(
            namespace
        )

    def key(
        self,
        key: Any,
    ) -> str:
        return normalize_key(
            key,
            namespace=self.namespace,
        )

    def get(
        self,
        key: Any,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        return self.cache.get(
            self.key(key),
            default,
            **kwargs,
        )

    def set(
        self,
        key: Any,
        value: V,
        **kwargs: Any,
    ) -> V:
        return self.cache.set(
            self.key(key),
            value,
            **kwargs,
        )

    def add(
        self,
        key: Any,
        value: V,
        **kwargs: Any,
    ) -> bool:
        return self.cache.add(
            self.key(key),
            value,
            **kwargs,
        )

    def replace(
        self,
        key: Any,
        value: V,
        **kwargs: Any,
    ) -> bool:
        return self.cache.replace(
            self.key(key),
            value,
            **kwargs,
        )

    def delete(
        self,
        key: Any,
    ) -> bool:
        return self.cache.delete(
            self.key(key)
        )

    def contains(
        self,
        key: Any,
    ) -> bool:
        return self.cache.contains(
            self.key(key)
        )

    def get_or_set(
        self,
        key: Any,
        factory: Callable[[], V],
        **kwargs: Any,
    ) -> V:
        return self.cache.get_or_set(
            self.key(key),
            factory,
            **kwargs,
        )

    def invalidate_prefix(
        self,
        prefix: str,
    ) -> int:
        return self.cache.invalidate_prefix(
            self.key(prefix)
        )

    def clear(self) -> int:
        return self.invalidate_prefix("")

    def keys(self) -> list[str]:
        prefix = self.namespace + ":"

        return [
            key[len(prefix):]
            for key in self.cache.keys()
            if key.startswith(prefix)
        ]

    def items(self) -> list[tuple[str, V]]:
        prefix = self.namespace + ":"

        return [
            (
                key[len(prefix):],
                value,
            )
            for key, value in self.cache.items()
            if key.startswith(prefix)
        ]

    def __contains__(
        self,
        key: object,
    ) -> bool:
        return self.contains(key)

    def __getitem__(
        self,
        key: Any,
    ) -> Any:
        return self.get(key)

    def __setitem__(
        self,
        key: Any,
        value: Any,
    ) -> None:
        self.set(
            key,
            value,
        )


# ============================================================================
# Decorators
# ============================================================================

def _call_key(
    function: Callable[..., Any],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
) -> str:
    try:
        payload = pickle.dumps(
            (
                function.__module__,
                function.__qualname__,
                args,
                tuple(
                    sorted(
                        kwargs.items()
                    )
                ),
            ),
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    except Exception:
        payload = repr(
            (
                function.__module__,
                function.__qualname__,
                args,
                sorted(kwargs.items()),
            )
        ).encode()

    digest = hashlib.sha256(
        payload
    ).hexdigest()

    return (
        f"{function.__module__}:"
        f"{function.__qualname__}:"
        f"{digest}"
    )


def memory_cached(
    cache: MemoryCache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
    tags: Iterable[str] = (),
    protected: bool = False,
) -> Callable[
    [Callable[P, T]],
    Callable[P, T],
]:
    """Decorator for caching synchronous function results."""

    def decorator(
        function: Callable[P, T],
    ) -> Callable[P, T]:
        @functools.wraps(function)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> T:
            key = (
                key_builder(
                    *args,
                    **kwargs,
                )
                if key_builder is not None
                else _call_key(
                    function,
                    args,
                    kwargs,
                )
            )

            sentinel = object()
            value = cache.get(
                key,
                sentinel,
            )

            if value is not sentinel:
                return value

            result = function(
                *args,
                **kwargs,
            )

            cache.set(
                key,
                result,
                ttl=ttl,
                tags=tags,
                protected=protected,
            )

            return result

        return wrapper

    return decorator


def memory_async_cached(
    cache: MemoryCache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
    tags: Iterable[str] = (),
    protected: bool = False,
) -> Callable[
    [Callable[P, Any]],
    Callable[P, Any],
]:
    """Decorator for caching async function results."""

    def decorator(
        function: Callable[P, Any],
    ) -> Callable[P, Any]:
        @functools.wraps(function)
        async def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Any:
            key = (
                key_builder(
                    *args,
                    **kwargs,
                )
                if key_builder is not None
                else _call_key(
                    function,
                    args,
                    kwargs,
                )
            )

            sentinel = object()
            value = cache.get(
                key,
                sentinel,
            )

            if value is not sentinel:
                return value

            result = function(
                *args,
                **kwargs,
            )

            if inspect.isawaitable(result):
                result = await result

            cache.set(
                key,
                result,
                ttl=ttl,
                tags=tags,
                protected=protected,
            )

            return result

        return wrapper

    return decorator


# ============================================================================
# Module-level default memory cache
# ============================================================================

default_memory_cache = MemoryCache[Any]()


def get(
    key: Any,
    default: Any = None,
    **kwargs: Any,
) -> Any:
    """Read from the default memory cache."""
    return default_memory_cache.get(
        key,
        default,
        **kwargs,
    )


def set(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> Any:
    """Write to the default memory cache."""
    return default_memory_cache.set(
        key,
        value,
        **kwargs,
    )


def add(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Add to the default memory cache."""
    return default_memory_cache.add(
        key,
        value,
        **kwargs,
    )


def replace(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Replace in the default memory cache."""
    return default_memory_cache.replace(
        key,
        value,
        **kwargs,
    )


def delete(
    key: Any,
) -> bool:
    """Delete from the default memory cache."""
    return default_memory_cache.delete(
        key
    )


def clear() -> int:
    """Clear the default memory cache."""
    return default_memory_cache.clear()


def exists(
    key: Any,
) -> bool:
    """Check the default memory cache."""
    return default_memory_cache.contains(
        key
    )


def get_or_set(
    key: Any,
    factory: Callable[[], T],
    **kwargs: Any,
) -> T:
    """Get or compute in the default memory cache."""
    return default_memory_cache.get_or_set(
        key,
        factory,
        **kwargs,
    )


def stats() -> dict[str, Any]:
    """Return default memory-cache statistics."""
    return default_memory_cache.stats_snapshot()


def health() -> bool:
    """Return default memory-cache health."""
    return default_memory_cache.health()


def cleanup() -> int:
    """Clean expired entries from the default memory cache."""
    return default_memory_cache.cleanup_expired()


def namespace(
    name: str,
) -> MemoryCacheNamespace[Any]:
    """Create a namespace over the default memory cache."""
    return default_memory_cache.scoped(
        name
    )


# ============================================================================
# Factory helpers
# ============================================================================

def create_memory_cache(
    *,
    namespace: str = DEFAULT_MEMORY_NAMESPACE,
    default_ttl: float | None = DEFAULT_MEMORY_TTL,
    max_entries: int = DEFAULT_MEMORY_MAX_ENTRIES,
    max_bytes: int = DEFAULT_MEMORY_MAX_BYTES,
    eviction_policy: MemoryEvictionPolicy | str = (
        MemoryEvictionPolicy.LRU
    ),
    allow_stale: bool = False,
    stale_grace: float = 0.0,
    copy_values: bool = False,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    compaction_interval: int = DEFAULT_COMPACTION_INTERVAL,
    lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
) -> MemoryCache[Any]:
    """Create a configured MemoryCache."""
    return MemoryCache(
        namespace=namespace,
        default_ttl=default_ttl,
        max_entries=max_entries,
        max_bytes=max_bytes,
        eviction_policy=eviction_policy,
        allow_stale=allow_stale,
        stale_grace=stale_grace,
        copy_values=copy_values,
        sample_size=sample_size,
        compaction_interval=compaction_interval,
        lock_timeout=lock_timeout,
    )


def create_unbounded_memory_cache(
    *,
    namespace: str = DEFAULT_MEMORY_NAMESPACE,
    default_ttl: float | None = None,
    **kwargs: Any,
) -> MemoryCache[Any]:
    """Create a cache without entry or byte capacity limits."""
    return MemoryCache(
        namespace=namespace,
        default_ttl=default_ttl,
        max_entries=0,
        max_bytes=0,
        **kwargs,
    )


def create_test_memory_cache(
    **kwargs: Any,
) -> MemoryCache[Any]:
    """Create a deterministic-friendly test cache."""
    return MemoryCache(
        namespace=kwargs.pop(
            "namespace",
            "test-memory",
        ),
        default_ttl=kwargs.pop(
            "default_ttl",
            None,
        ),
        max_entries=kwargs.pop(
            "max_entries",
            0,
        ),
        max_bytes=kwargs.pop(
            "max_bytes",
            0,
        ),
        **kwargs,
    )


# ============================================================================
# Comparison and migration helpers
# ============================================================================

def copy_to_memory(
    source: Mapping[Any, V],
    target: MemoryCache[V],
    *,
    ttl: float | None = None,
    tags: Iterable[str] = (),
    protected: bool = False,
) -> int:
    """Copy mapping values into a memory cache."""
    count = 0

    for key, value in source.items():
        target.set(
            key,
            value,
            ttl=ttl,
            tags=tags,
            protected=protected,
        )
        count += 1

    return count


def export_mapping(
    cache: MemoryCache[V],
    *,
    include_expired: bool = False,
) -> dict[str, V]:
    """Export cache contents as a plain mapping."""
    return dict(
        cache.items(
            include_expired=include_expired
        )
    )


def import_mapping(
    cache: MemoryCache[V],
    values: Mapping[Any, V],
    *,
    clear_first: bool = False,
    ttl: float | None = None,
) -> int:
    """Import a mapping into a memory cache."""
    if clear_first:
        cache.clear()

    return cache.set_many(
        values,
        ttl=ttl,
    )


def cache_fingerprint(
    cache: MemoryCache[Any],
) -> str:
    """Generate a fingerprint from memory-cache metadata."""
    records = []

    for entry in sorted(
        cache.entries(
            include_expired=False
        ),
        key=lambda item: item.key,
    ):
        records.append(
            "|".join([
                entry.key,
                str(entry.version),
                str(entry.size),
                str(entry.access_count),
                str(entry.generation),
            ])
        )

    return hashlib.sha256(
        "\n".join(records).encode("utf-8")
    ).hexdigest()


# ============================================================================
# Public exports
# ============================================================================

__all__ = [
    "DEFAULT_MEMORY_MAX_ENTRIES",
    "DEFAULT_MEMORY_MAX_BYTES",
    "DEFAULT_MEMORY_TTL",
    "DEFAULT_SAMPLE_SIZE",
    "DEFAULT_COMPACTION_INTERVAL",
    "DEFAULT_LOCK_TIMEOUT",
    "DEFAULT_MEMORY_NAMESPACE",
    "MemoryCacheError",
    "MemoryCapacityError",
    "MemoryPolicyError",
    "MemorySnapshotError",
    "MemoryEvictionPolicy",
    "MemoryEntryState",
    "MemoryCacheConfig",
    "MemoryEntry",
    "MemoryStats",
    "MemorySnapshot",
    "MemoryCacheInfo",
    "MemoryCache",
    "MemoryCacheNamespace",
    "memory_cached",
    "memory_async_cached",
    "default_memory_cache",
    "get",
    "set",
    "add",
    "replace",
    "delete",
    "clear",
    "exists",
    "get_or_set",
    "stats",
    "health",
    "cleanup",
    "namespace",
    "create_memory_cache",
    "create_unbounded_memory_cache",
    "create_test_memory_cache",
    "copy_to_memory",
    "export_mapping",
    "import_mapping",
    "cache_fingerprint",
]