"""
AURA Foundation - Cache Core.

A production-oriented, thread-safe cache abstraction used by the AURA
foundation caching subsystem.

The module provides:

* cache entries with TTL and stale-state handling
* LRU-style memory management
* optional size limits
* namespaces
* cache statistics and hit-rate tracking
* cache events and listeners
* key normalization and namespacing
* get/set/add/replace/delete semantics
* bulk operations
* get-or-set and compute-if-absent helpers
* compare-and-set support
* versioned values
* tags and tag-based invalidation
* predicate-based invalidation
* snapshots and restoration
* import/export helpers
* cache decorators
* synchronous and asynchronous convenience APIs
* locking around expensive cache fills
* negative caching
* serialization hooks
* admission and eviction hooks
* health information
* lifecycle management
* configurable clock abstraction
* test-friendly isolated operation

The implementation deliberately keeps storage concerns separate from the
cache policy. MemoryCache and DiskCache can therefore build on the same
public contracts without duplicating the high-level cache behavior.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import hashlib
import inspect
import json
import pickle
import threading
import time
from collections import OrderedDict, defaultdict
from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, ParamSpec, Protocol, TypeVar


# ============================================================================
# Public constants
# ============================================================================

DEFAULT_TTL = 3600.0
DEFAULT_MAX_ENTRIES = 10_000
DEFAULT_MAX_SIZE = 0
DEFAULT_NAMESPACE = "default"
DEFAULT_VERSION = 1
DEFAULT_LOCK_TIMEOUT = 30.0
DEFAULT_STATS_WINDOW = 60.0

P = ParamSpec("P")
T = TypeVar("T")
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


# ============================================================================
# Exceptions
# ============================================================================

class CacheError(Exception):
    """Base exception for all cache errors."""


class CacheKeyError(CacheError, ValueError):
    """Raised when a cache key is invalid."""


class CacheSerializationError(CacheError):
    """Raised when cache value serialization fails."""


class CacheCapacityError(CacheError):
    """Raised when a cache cannot accept an item."""


class CacheFrozenError(CacheError):
    """Raised when mutation is attempted on a frozen cache."""


class CacheClosedError(CacheError):
    """Raised when an operation is attempted after cache shutdown."""


class CacheLockTimeout(CacheError, TimeoutError):
    """Raised when a cache fill lock cannot be acquired in time."""


class CacheVersionError(CacheError):
    """Raised when a version constraint fails."""


class CacheConfigurationError(CacheError, ValueError):
    """Raised when cache configuration is invalid."""


# ============================================================================
# Enums
# ============================================================================

class CacheEventType(StrEnum):
    """Events emitted by a cache."""

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
    """Reasons for an entry to leave a cache."""

    CAPACITY = "capacity"
    EXPIRED = "expired"
    EXPLICIT = "explicit"
    INVALIDATED = "invalidated"
    CLEAR = "clear"
    REPLACED = "replaced"


class CacheState(StrEnum):
    """Lifecycle states."""

    NEW = "new"
    READY = "ready"
    FROZEN = "frozen"
    CLOSED = "closed"


# ============================================================================
# Protocols
# ============================================================================

class Clock(Protocol):
    """Protocol for obtaining monotonic time."""

    def __call__(self) -> float:
        ...


class ValueSerializer(Protocol):
    """Protocol for cache value serialization."""

    def dumps(self, value: Any) -> bytes:
        ...

    def loads(self, payload: bytes) -> Any:
        ...


class AdmissionPolicy(Protocol):
    """Protocol deciding whether a value may enter the cache."""

    def admit(
        self,
        key: str,
        value: Any,
    ) -> bool:
        ...


class EvictionListener(Protocol):
    """Protocol for eviction callbacks."""

    def __call__(
        self,
        key: str,
        value: Any,
        reason: EvictionReason,
    ) -> None:
        ...


# ============================================================================
# Serialization adapters
# ============================================================================

class PickleSerializer:
    """Safe internal adapter around pickle.

    Applications should only use this with trusted cache data. The cache
    itself does not deserialize arbitrary network input.
    """

    def dumps(self, value: Any) -> bytes:
        try:
            return pickle.dumps(
                value,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise CacheSerializationError(
                f"Unable to serialize cache value: {type(value).__name__}"
            ) from exc

    def loads(self, payload: bytes) -> Any:
        try:
            return pickle.loads(payload)
        except Exception as exc:
            raise CacheSerializationError(
                "Unable to deserialize cache value."
            ) from exc


class JsonSerializer:
    """JSON serializer for cache-safe primitive values."""

    def dumps(self, value: Any) -> bytes:
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise CacheSerializationError(
                f"Value is not JSON serializable: {type(value).__name__}"
            ) from exc

    def loads(self, payload: bytes) -> Any:
        try:
            return json.loads(
                payload.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CacheSerializationError(
                "Invalid JSON cache payload."
            ) from exc


# ============================================================================
# Utility functions
# ============================================================================

def monotonic_time() -> float:
    """Return the monotonic process clock."""
    return time.monotonic()


def normalize_namespace(namespace: str | None) -> str:
    """Normalize a cache namespace."""
    if namespace is None:
        return DEFAULT_NAMESPACE

    value = str(namespace).strip()

    if not value:
        return DEFAULT_NAMESPACE

    return value


def normalize_key(
    key: Any,
    *,
    namespace: str | None = None,
) -> str:
    """Convert a cache key into a deterministic string."""
    if key is None:
        raise CacheKeyError("Cache key cannot be None.")

    if isinstance(key, bytes):
        try:
            base = key.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CacheKeyError(
                "Byte cache keys must be valid UTF-8."
            ) from exc
    elif isinstance(key, str):
        base = key
    elif isinstance(key, (int, float, bool)):
        base = str(key)
    else:
        try:
            base = repr(key)
        except Exception as exc:
            raise CacheKeyError(
                "Unable to represent cache key."
            ) from exc

    base = base.strip()

    if not base:
        raise CacheKeyError("Cache key cannot be empty.")

    ns = normalize_namespace(namespace)

    if ns:
        return f"{ns}:{base}"

    return base


def make_key(
    *parts: Any,
    namespace: str | None = None,
    separator: str = ":",
) -> str:
    """Create a deterministic cache key from multiple components."""
    if not parts:
        raise CacheKeyError("At least one key component is required.")

    normalized = [
        str(part).strip()
        for part in parts
    ]

    if any(not item for item in normalized):
        raise CacheKeyError("Cache key components cannot be empty.")

    base = separator.join(normalized)

    return normalize_key(
        base,
        namespace=namespace,
    )


def hash_key(
    key: Any,
    *,
    algorithm: str = "sha256",
) -> str:
    """Return a stable hexadecimal digest for a cache key."""
    normalized = normalize_key(key)

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise CacheConfigurationError(
            f"Unsupported hash algorithm: {algorithm}"
        ) from exc

    digest.update(
        normalized.encode("utf-8")
    )

    return digest.hexdigest()


def estimate_size(value: Any) -> int:
    """Estimate the in-memory size of a cache value.

    This intentionally favors a conservative, dependency-free approximation.
    """
    try:
        return len(
            pickle.dumps(
                value,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        )
    except Exception:
        try:
            return len(repr(value).encode("utf-8"))
        except Exception:
            return 1


# ============================================================================
# Cache records
# ============================================================================

@dataclass
class CacheEntry(Generic[V]):
    """Stored cache value plus policy metadata."""

    key: str
    value: V
    created_at: float
    expires_at: float | None = None
    accessed_at: float = field(default_factory=monotonic_time)
    access_count: int = 0
    size: int = 0
    version: int = DEFAULT_VERSION
    tags: frozenset[str] = frozenset()
    stale: bool = False
    negative: bool = False

    def is_expired(
        self,
        now: float | None = None,
    ) -> bool:
        if self.expires_at is None:
            return False

        current = (
            monotonic_time()
            if now is None
            else now
        )

        return current >= self.expires_at

    def remaining_ttl(
        self,
        now: float | None = None,
    ) -> float | None:
        if self.expires_at is None:
            return None

        current = (
            monotonic_time()
            if now is None
            else now
        )

        return max(
            0.0,
            self.expires_at - current,
        )

    def touch(
        self,
        now: float | None = None,
    ) -> None:
        self.accessed_at = (
            monotonic_time()
            if now is None
            else now
        )
        self.access_count += 1

    def clone(self) -> "CacheEntry[V]":
        return CacheEntry(
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
        )


@dataclass(frozen=True)
class CacheEvent:
    """Immutable event emitted by a cache."""

    event_type: CacheEventType
    key: str | None
    timestamp: float
    namespace: str
    value: Any = None
    reason: EvictionReason | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def safe_value(
        self,
        *,
        reveal: bool = False,
    ) -> Any:
        if reveal:
            return self.value
        return None


@dataclass
class CacheStats:
    """Runtime cache statistics."""

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
    bytes_written: int = 0
    bytes_read: int = 0
    compute_calls: int = 0
    compute_waits: int = 0
    negative_hits: int = 0

    started_at: float = field(
        default_factory=time.time
    )

    def record_hit(
        self,
        *,
        negative: bool = False,
    ) -> None:
        self.hits += 1
        if negative:
            self.negative_hits += 1

    def record_miss(self) -> None:
        self.misses += 1

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.hits / self.requests

    @property
    def miss_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.misses / self.requests

    @property
    def uptime(self) -> float:
        return max(
            0.0,
            time.time() - self.started_at,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "requests": self.requests,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "sets": self.sets,
            "adds": self.adds,
            "replaces": self.replaces,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "invalidations": self.invalidations,
            "clears": self.clears,
            "errors": self.errors,
            "bytes_written": self.bytes_written,
            "bytes_read": self.bytes_read,
            "compute_calls": self.compute_calls,
            "compute_waits": self.compute_waits,
            "negative_hits": self.negative_hits,
            "started_at": self.started_at,
            "uptime": self.uptime,
        }

    def reset(self) -> None:
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.adds = 0
        self.replaces = 0
        self.deletes = 0
        self.evictions = 0
        self.expirations = 0
        self.invalidations = 0
        self.clears = 0
        self.errors = 0
        self.bytes_written = 0
        self.bytes_read = 0
        self.compute_calls = 0
        self.compute_waits = 0
        self.negative_hits = 0
        self.started_at = time.time()


@dataclass(frozen=True)
class CacheSnapshot:
    """Serializable snapshot of cache contents."""

    namespace: str
    created_at: float
    entries: tuple[CacheEntry[Any], ...]
    stats: Mapping[str, Any]

    @property
    def size(self) -> int:
        return len(self.entries)

    def keys(self) -> tuple[str, ...]:
        return tuple(
            entry.key
            for entry in self.entries
        )


@dataclass(frozen=True)
class CacheConfig:
    """Validated cache configuration."""

    namespace: str = DEFAULT_NAMESPACE
    default_ttl: float | None = DEFAULT_TTL
    max_entries: int = DEFAULT_MAX_ENTRIES
    max_size: int = DEFAULT_MAX_SIZE
    allow_stale: bool = False
    copy_values: bool = False
    negative_ttl: float | None = None
    lock_timeout: float = DEFAULT_LOCK_TIMEOUT
    serializer: ValueSerializer | None = None

    def validate(self) -> None:
        if self.default_ttl is not None and self.default_ttl < 0:
            raise CacheConfigurationError(
                "default_ttl cannot be negative."
            )

        if self.max_entries < 0:
            raise CacheConfigurationError(
                "max_entries cannot be negative."
            )

        if self.max_size < 0:
            raise CacheConfigurationError(
                "max_size cannot be negative."
            )

        if self.negative_ttl is not None and self.negative_ttl < 0:
            raise CacheConfigurationError(
                "negative_ttl cannot be negative."
            )

        if self.lock_timeout < 0:
            raise CacheConfigurationError(
                "lock_timeout cannot be negative."
            )


# ============================================================================
# Core cache implementation
# ============================================================================

class Cache(Generic[V]):
    """Thread-safe in-process cache with configurable eviction policy."""

    def __init__(
        self,
        *,
        namespace: str = DEFAULT_NAMESPACE,
        default_ttl: float | None = DEFAULT_TTL,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_size: int = DEFAULT_MAX_SIZE,
        allow_stale: bool = False,
        copy_values: bool = False,
        negative_ttl: float | None = None,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        serializer: ValueSerializer | None = None,
        clock: Clock = monotonic_time,
        admission_policy: AdmissionPolicy | None = None,
    ) -> None:
        self.config = CacheConfig(
            namespace=normalize_namespace(namespace),
            default_ttl=default_ttl,
            max_entries=max_entries,
            max_size=max_size,
            allow_stale=allow_stale,
            copy_values=copy_values,
            negative_ttl=negative_ttl,
            lock_timeout=lock_timeout,
            serializer=serializer,
        )
        self.config.validate()

        self._clock = clock
        self._admission_policy = admission_policy

        self._entries: OrderedDict[
            str,
            CacheEntry[V],
        ] = OrderedDict()

        self._tags: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        self._lock = threading.RLock()
        self._compute_locks: dict[
            str,
            threading.Lock,
        ] = {}

        self._listeners: list[
            Callable[[CacheEvent], None]
        ] = []

        self._eviction_listeners: list[
            EvictionListener
        ] = []

        self._stats = CacheStats()
        self._state = CacheState.NEW
        self._total_size = 0

        self.initialize()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def state(self) -> CacheState:
        with self._lock:
            return self._state

    @property
    def namespace(self) -> str:
        return self.config.namespace

    @property
    def stats(self) -> CacheStats:
        return self._stats

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def total_size(self) -> int:
        with self._lock:
            return self._total_size

    def initialize(self) -> None:
        with self._lock:
            if self._state == CacheState.CLOSED:
                raise CacheClosedError(
                    "Cannot initialize a closed cache."
                )
            self._state = CacheState.READY

    def close(self) -> None:
        with self._lock:
            if self._state == CacheState.CLOSED:
                return
            self._entries.clear()
            self._tags.clear()
            self._compute_locks.clear()
            self._total_size = 0
            self._state = CacheState.CLOSED

    def shutdown(self) -> None:
        self.close()

    def freeze(self) -> None:
        with self._lock:
            self._ensure_open()
            self._state = CacheState.FROZEN

    def unfreeze(self) -> None:
        with self._lock:
            self._ensure_open()
            self._state = CacheState.READY

    def reset(self) -> None:
        self._ensure_mutable()
        self.clear()
        self._stats.reset()

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def key(
        self,
        key: Any,
    ) -> str:
        return normalize_key(
            key,
            namespace=self.namespace,
        )

    def composite_key(
        self,
        *parts: Any,
    ) -> str:
        return make_key(
            *parts,
            namespace=self.namespace,
        )

    def key_hash(
        self,
        key: Any,
    ) -> str:
        return hash_key(
            self.key(key)
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_open(self) -> None:
        if self._state == CacheState.CLOSED:
            raise CacheClosedError(
                "Cache is closed."
            )

    def _ensure_mutable(self) -> None:
        self._ensure_open()
        if self._state == CacheState.FROZEN:
            raise CacheFrozenError(
                "Cache is frozen."
            )

    def _now(self) -> float:
        return float(self._clock())

    def _ttl(
        self,
        ttl: float | None,
    ) -> float | None:
        selected = (
            self.config.default_ttl
            if ttl is None
            else ttl
        )

        if selected is None:
            return None

        if selected < 0:
            raise CacheConfigurationError(
                "TTL cannot be negative."
            )

        if selected == 0:
            return self._now()

        return self._now() + selected

    def _prepare_value(
        self,
        value: V,
    ) -> V:
        if not self.config.copy_values:
            return value

        try:
            return pickle.loads(
                pickle.dumps(
                    value,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            )
        except Exception:
            return value

    def _entry_size(
        self,
        value: V,
    ) -> int:
        if self.config.serializer is not None:
            try:
                return len(
                    self.config.serializer.dumps(value)
                )
            except Exception as exc:
                raise CacheSerializationError(
                    "Unable to estimate serialized cache value size."
                ) from exc

        return estimate_size(value)

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
            value=value,
            reason=reason,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                continue

    def _remove_entry(
        self,
        normalized: str,
        *,
        reason: EvictionReason,
        emit: bool = True,
    ) -> CacheEntry[V] | None:
        entry = self._entries.pop(
            normalized,
            None,
        )

        if entry is None:
            return None

        self._total_size = max(
            0,
            self._total_size - entry.size,
        )

        for tag in entry.tags:
            keys = self._tags.get(tag)
            if keys is None:
                continue
            keys.discard(normalized)
            if not keys:
                self._tags.pop(tag, None)

        if reason == EvictionReason.CAPACITY:
            self._stats.evictions += 1
        elif reason == EvictionReason.EXPIRED:
            self._stats.expirations += 1

        if emit:
            event_type = (
                CacheEventType.EXPIRE
                if reason == EvictionReason.EXPIRED
                else CacheEventType.EVICT
            )

            self._emit(
                event_type,
                key=normalized,
                value=entry.value,
                reason=reason,
            )

            self._notify_eviction(
                normalized,
                entry.value,
                reason,
            )

        return entry

    def _notify_eviction(
        self,
        key: str,
        value: Any,
        reason: EvictionReason,
    ) -> None:
        with self._lock:
            listeners = list(
                self._eviction_listeners
            )

        for listener in listeners:
            try:
                listener(
                    key,
                    value,
                    reason,
                )
            except Exception:
                continue

    def _expire_if_needed(
        self,
        normalized: str,
        *,
        now: float | None = None,
    ) -> bool:
        entry = self._entries.get(
            normalized
        )

        if entry is None:
            return False

        current = (
            self._now()
            if now is None
            else now
        )

        if not entry.is_expired(current):
            return False

        if self.config.allow_stale:
            entry.stale = True
            return False

        self._remove_entry(
            normalized,
            reason=EvictionReason.EXPIRED,
        )
        return True

    def _touch(
        self,
        normalized: str,
        entry: CacheEntry[V],
    ) -> None:
        entry.touch(
            self._now()
        )
        self._entries.move_to_end(
            normalized
        )

    def _evict_if_needed(self) -> None:
        while True:
            too_many = (
                self.config.max_entries > 0
                and len(self._entries)
                > self.config.max_entries
            )

            too_large = (
                self.config.max_size > 0
                and self._total_size
                > self.config.max_size
            )

            if not too_many and not too_large:
                return

            if not self._entries:
                return

            oldest_key = next(
                iter(self._entries)
            )

            self._remove_entry(
                oldest_key,
                reason=EvictionReason.CAPACITY,
            )

    def _admit(
        self,
        normalized: str,
        value: V,
    ) -> bool:
        if self._admission_policy is None:
            return True

        try:
            return bool(
                self._admission_policy.admit(
                    normalized,
                    value,
                )
            )
        except Exception as exc:
            self._stats.errors += 1
            self._emit(
                CacheEventType.ERROR,
                key=normalized,
                metadata={
                    "operation": "admission",
                    "error": repr(exc),
                },
            )
            return False

    # ------------------------------------------------------------------
    # Core lookup
    # ------------------------------------------------------------------

    def get(
        self,
        key: Any,
        default: Any = None,
        *,
        allow_stale: bool | None = None,
    ) -> V | Any:
        self._ensure_open()

        normalized = self.key(key)

        with self._lock:
            self._stats.hits += 0
            self._emit(
                CacheEventType.GET,
                key=normalized,
            )

            entry = self._entries.get(
                normalized
            )

            if entry is None:
                self._stats.record_miss()
                self._emit(
                    CacheEventType.MISS,
                    key=normalized,
                )
                return default

            expired = entry.is_expired(
                self._now()
            )

            stale_allowed = (
                self.config.allow_stale
                if allow_stale is None
                else allow_stale
            )

            if expired and not stale_allowed:
                self._remove_entry(
                    normalized,
                    reason=EvictionReason.EXPIRED,
                )
                self._stats.record_miss()
                self._emit(
                    CacheEventType.MISS,
                    key=normalized,
                )
                return default

            if expired:
                entry.stale = True

            self._touch(
                normalized,
                entry,
            )
            self._stats.record_hit(
                negative=entry.negative
            )

            self._emit(
                CacheEventType.HIT,
                key=normalized,
                metadata={
                    "stale": entry.stale,
                    "version": entry.version,
                },
            )

            value = entry.value

            if self.config.copy_values:
                return self._prepare_value(value)

            return value

    def require(
        self,
        key: Any,
        *,
        allow_stale: bool | None = None,
    ) -> V:
        value = self.get(
            key,
            None,
            allow_stale=allow_stale,
        )

        if value is None:
            raise KeyError(
                self.key(key)
            )

        return value

    def peek(
        self,
        key: Any,
        default: Any = None,
    ) -> Any:
        """Read without changing LRU order or access counters."""
        self._ensure_open()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return default

            if (
                entry.is_expired(self._now())
                and not self.config.allow_stale
            ):
                return default

            return entry.value

    def contains(
        self,
        key: Any,
        *,
        allow_stale: bool | None = None,
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

    def __contains__(
        self,
        key: object,
    ) -> bool:
        try:
            return self.contains(key)
        except CacheError:
            return False

    def __getitem__(
        self,
        key: Any,
    ) -> V:
        return self.require(key)

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def set(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        version: int | None = None,
        negative: bool = False,
    ) -> V:
        self._ensure_mutable()

        normalized = self.key(key)

        if not self._admit(
            normalized,
            value,
        ):
            raise CacheCapacityError(
                f"Admission policy rejected key '{normalized}'."
            )

        prepared = self._prepare_value(
            value
        )
        size = self._entry_size(
            prepared
        )

        now = self._now()

        if version is None:
            with self._lock:
                previous = self._entries.get(
                    normalized
                )
                version = (
                    previous.version + 1
                    if previous is not None
                    else DEFAULT_VERSION
                )

        tag_set = frozenset(
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        )

        entry = CacheEntry(
            key=normalized,
            value=prepared,
            created_at=now,
            expires_at=self._ttl(
                (
                    self.config.negative_ttl
                    if negative
                    and self.config.negative_ttl is not None
                    else ttl
                )
            ),
            accessed_at=now,
            access_count=0,
            size=size,
            version=version,
            tags=tag_set,
            stale=False,
            negative=negative,
        )

        with self._lock:
            previous = self._entries.get(
                normalized
            )

            if previous is not None:
                self._total_size = max(
                    0,
                    self._total_size - previous.size,
                )

                for tag in previous.tags:
                    self._tags[tag].discard(
                        normalized
                    )

            self._entries[
                normalized
            ] = entry
            self._entries.move_to_end(
                normalized
            )

            self._total_size += size
            self._stats.sets += 1
            self._stats.bytes_written += size

            for tag in tag_set:
                self._tags[tag].add(
                    normalized
                )

            self._evict_if_needed()

        self._emit(
            CacheEventType.SET,
            key=normalized,
            metadata={
                "ttl": (
                    entry.remaining_ttl(now)
                ),
                "version": entry.version,
                "negative": negative,
                "size": size,
            },
        )

        return prepared

    def add(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        negative: bool = False,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            if normalized in self._entries:
                if self._expire_if_needed(normalized):
                    pass
                else:
                    return False

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
            negative=negative,
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
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            if normalized not in self._entries:
                return False

            if self._expire_if_needed(normalized):
                return False

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
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
        existing = self.get(
            key,
            None,
        )

        if existing is not None:
            return existing

        self.set(
            key,
            default,
            ttl=ttl,
            tags=tags,
        )

        return default

    def __setitem__(
        self,
        key: Any,
        value: V,
    ) -> None:
        self.set(
            key,
            value,
        )

    # ------------------------------------------------------------------
    # Delete and invalidation
    # ------------------------------------------------------------------

    def delete(
        self,
        key: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            removed = self._remove_entry(
                normalized,
                reason=EvictionReason.EXPLICIT,
                emit=False,
            )

            if removed is None:
                return False

            self._stats.deletes += 1

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
            entry = self._remove_entry(
                normalized,
                reason=EvictionReason.EXPLICIT,
                emit=False,
            )

            if entry is None:
                return default

            self._stats.deletes += 1

        self._emit(
            CacheEventType.DELETE,
            key=normalized,
        )

        return entry.value

    def invalidate_tag(
        self,
        tag: str,
    ) -> int:
        self._ensure_mutable()
        normalized_tag = str(tag).strip()

        if not normalized_tag:
            return 0

        with self._lock:
            keys = list(
                self._tags.get(
                    normalized_tag,
                    set(),
                )
            )

        count = 0

        for key in keys:
            with self._lock:
                entry = self._remove_entry(
                    key,
                    reason=EvictionReason.INVALIDATED,
                    emit=False,
                )

            if entry is not None:
                count += 1

        with self._lock:
            self._stats.invalidations += count

        if count:
            self._emit(
                CacheEventType.INVALIDATE,
                metadata={
                    "tag": normalized_tag,
                    "count": count,
                },
            )

        return count

    def invalidate(
        self,
        predicate: Callable[[str, CacheEntry[V]], bool],
    ) -> int:
        self._ensure_mutable()

        if not callable(predicate):
            raise TypeError(
                "predicate must be callable."
            )

        with self._lock:
            candidates = [
                (key, entry.clone())
                for key, entry
                in self._entries.items()
            ]

        count = 0

        for key, entry in candidates:
            try:
                matched = bool(
                    predicate(
                        key,
                        entry,
                    )
                )
            except Exception as exc:
                self._stats.errors += 1
                self._emit(
                    CacheEventType.ERROR,
                    key=key,
                    metadata={
                        "operation": "invalidate",
                        "error": repr(exc),
                    },
                )
                continue

            if not matched:
                continue

            with self._lock:
                removed = self._remove_entry(
                    key,
                    reason=EvictionReason.INVALIDATED,
                    emit=False,
                )

            if removed is not None:
                count += 1

        with self._lock:
            self._stats.invalidations += count

        return count

    def invalidate_prefix(
        self,
        prefix: str,
    ) -> int:
        normalized_prefix = str(prefix)

        return self.invalidate(
            lambda key, entry:
                key.startswith(normalized_prefix)
        )

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def get_many(
        self,
        keys: Iterable[Any],
        *,
        include_missing: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for key in keys:
            normalized = self.key(key)
            sentinel = object()
            value = self.get(
                normalized,
                sentinel,
            )

            if (
                include_missing
                or value is not sentinel
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

    def delete_many(
        self,
        keys: Iterable[Any],
    ) -> int:
        count = 0

        for key in keys:
            if self.delete(key):
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
    # Compute / fill helpers
    # ------------------------------------------------------------------

    def get_or_set(
        self,
        key: Any,
        factory: Callable[[], V],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        negative: bool = False,
    ) -> V:
        sentinel = object()
        cached = self.get(
            key,
            sentinel,
        )

        if cached is not sentinel:
            return cached

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        with self._fill_lock(key):
            cached = self.get(
                key,
                sentinel,
            )

            if cached is not sentinel:
                return cached

            self._stats.compute_calls += 1

            value = factory()

            self.set(
                key,
                value,
                ttl=ttl,
                tags=tags,
                negative=negative,
            )

            return value

    async def aget_or_set(
        self,
        key: Any,
        factory: Callable[[], Any],
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        negative: bool = False,
    ) -> V:
        sentinel = object()
        cached = self.get(
            key,
            sentinel,
        )

        if cached is not sentinel:
            return cached

        lock = self._get_compute_lock(
            self.key(key)
        )

        acquired = lock.acquire(
            timeout=self.config.lock_timeout
        )

        if not acquired:
            raise CacheLockTimeout(
                f"Timed out waiting for cache key '{self.key(key)}'."
            )

        try:
            cached = self.get(
                key,
                sentinel,
            )

            if cached is not sentinel:
                return cached

            self._stats.compute_calls += 1

            result = factory()

            if inspect.isawaitable(result):
                value = await result
            else:
                value = result

            self.set(
                key,
                value,
                ttl=ttl,
                tags=tags,
                negative=negative,
            )

            return value
        finally:
            lock.release()

    @contextlib.contextmanager
    def _fill_lock(
        self,
        key: Any,
    ) -> Iterator[None]:
        normalized = self.key(key)
        lock = self._get_compute_lock(
            normalized
        )

        acquired = lock.acquire(
            timeout=self.config.lock_timeout
        )

        if not acquired:
            raise CacheLockTimeout(
                f"Timed out waiting for cache key '{normalized}'."
            )

        try:
            yield
        finally:
            lock.release()

    def _get_compute_lock(
        self,
        normalized: str,
    ) -> threading.Lock:
        with self._lock:
            lock = self._compute_locks.get(
                normalized
            )

            if lock is None:
                lock = threading.Lock()
                self._compute_locks[
                    normalized
                ] = lock

            return lock

    # ------------------------------------------------------------------
    # Versioning and CAS
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

            if entry.is_expired(self._now()):
                if not self.config.allow_stale:
                    self._remove_entry(
                        normalized,
                        reason=EvictionReason.EXPIRED,
                    )
                    return None

            return entry.version

    def compare_and_set(
        self,
        key: Any,
        expected_version: int | None,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
    ) -> int:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            current = self._entries.get(
                normalized
            )

            current_version = (
                None
                if current is None
                else current.version
            )

            if current_version != expected_version:
                raise CacheVersionError(
                    f"Version mismatch for '{normalized}': "
                    f"expected {expected_version!r}, "
                    f"actual {current_version!r}."
                )

            new_version = (
                1
                if current is None
                else current.version + 1
            )

        self.set(
            normalized,
            value,
            ttl=ttl,
            tags=tags,
            version=new_version,
        )

        return new_version

    def get_with_version(
        self,
        key: Any,
    ) -> tuple[V | None, int | None]:
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return None, None

            if (
                entry.is_expired(self._now())
                and not self.config.allow_stale
            ):
                self._remove_entry(
                    normalized,
                    reason=EvictionReason.EXPIRED,
                )
                return None, None

            self._touch(
                normalized,
                entry,
            )

            return (
                entry.value,
                entry.version,
            )

    # ------------------------------------------------------------------
    # TTL operations
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

            return entry.remaining_ttl(
                self._now()
            )

    def expire(
        self,
        key: Any,
        ttl: float,
    ) -> bool:
        self._ensure_mutable()
        normalized = self.key(key)

        with self._lock:
            entry = self._entries.get(
                normalized
            )

            if entry is None:
                return False

            entry.expires_at = self._ttl(
                ttl
            )
            entry.stale = False

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

            return True

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup_expired(
        self,
        *,
        limit: int | None = None,
    ) -> int:
        self._ensure_mutable()

        with self._lock:
            candidates = list(
                self._entries.items()
            )

        removed = 0
        now = self._now()

        for key, entry in candidates:
            if (
                limit is not None
                and removed >= limit
            ):
                break

            if not entry.is_expired(now):
                continue

            with self._lock:
                result = self._remove_entry(
                    key,
                    reason=EvictionReason.EXPIRED,
                )

            if result is not None:
                removed += 1

        return removed

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

            for key in list(self._entries):
                self._remove_entry(
                    key,
                    reason=EvictionReason.CLEAR,
                    emit=False,
                )

            self._entries.clear()
            self._tags.clear()
            self._total_size = 0
            self._stats.clears += 1

        if emit:
            self._emit(
                CacheEventType.CLEAR,
                metadata={
                    "count": count,
                },
            )

        return count

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
        keys = self.keys(
            include_expired=include_expired
        )

        return [
            self.peek(key)
            for key in keys
        ]

    def items(
        self,
        *,
        include_expired: bool = False,
    ) -> list[tuple[str, V]]:
        keys = self.keys(
            include_expired=include_expired
        )

        return [
            (
                key,
                self.peek(key),
            )
            for key in keys
        ]

    def entries(
        self,
        *,
        include_expired: bool = True,
    ) -> list[CacheEntry[V]]:
        self._ensure_open()

        if not include_expired:
            self.cleanup_expired()

        with self._lock:
            return [
                entry.clone()
                for entry
                in self._entries.values()
            ]

    def __iter__(self) -> Iterator[str]:
        return iter(
            self.keys()
        )

    def __len__(self) -> int:
        return self.size

    # ------------------------------------------------------------------
    # Snapshot / restore
    # ------------------------------------------------------------------

    def snapshot(self) -> CacheSnapshot:
        self._ensure_open()

        with self._lock:
            entries = tuple(
                entry.clone()
                for entry
                in self._entries.values()
            )

            stats = self._stats.snapshot()

        return CacheSnapshot(
            namespace=self.namespace,
            created_at=time.time(),
            entries=entries,
            stats=stats,
        )

    def restore(
        self,
        snapshot: CacheSnapshot,
        *,
        clear_first: bool = True,
    ) -> int:
        self._ensure_mutable()

        if snapshot.namespace != self.namespace:
            raise CacheConfigurationError(
                "Snapshot namespace does not match cache namespace."
            )

        if clear_first:
            self.clear(
                emit=False
            )

        count = 0

        for entry in snapshot.entries:
            if entry.is_expired(
                self._now()
            ):
                continue

            with self._lock:
                self._entries[
                    entry.key
                ] = entry.clone()
                self._total_size += entry.size

                for tag in entry.tags:
                    self._tags[tag].add(
                        entry.key
                    )

            count += 1

        self._evict_if_needed()

        self._emit(
            CacheEventType.RESTORE,
            metadata={
                "count": count,
            },
        )

        return count

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def export_bytes(self) -> bytes:
        snapshot = self.snapshot()

        try:
            return pickle.dumps(
                snapshot,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise CacheSerializationError(
                "Unable to export cache snapshot."
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
            raise CacheSerializationError(
                "Unable to import cache snapshot."
            ) from exc

        if not isinstance(
            snapshot,
            CacheSnapshot,
        ):
            raise CacheSerializationError(
                "Payload does not contain a CacheSnapshot."
            )

        return self.restore(
            snapshot,
            clear_first=clear_first,
        )

    def export_json(
        self,
        *,
        reveal_values: bool = True,
    ) -> str:
        snapshot = self.snapshot()

        entries = []

        for entry in snapshot.entries:
            value = entry.value

            if (
                self.config.serializer is not None
                and not reveal_values
            ):
                value = None

            entries.append({
                "key": entry.key,
                "value": value,
                "created_at": entry.created_at,
                "expires_at": entry.expires_at,
                "accessed_at": entry.accessed_at,
                "access_count": entry.access_count,
                "size": entry.size,
                "version": entry.version,
                "tags": sorted(entry.tags),
                "stale": entry.stale,
                "negative": entry.negative,
            })

        try:
            return json.dumps(
                {
                    "namespace": snapshot.namespace,
                    "created_at": snapshot.created_at,
                    "entries": entries,
                    "stats": dict(snapshot.stats),
                },
                ensure_ascii=False,
                default=str,
            )
        except (TypeError, ValueError) as exc:
            raise CacheSerializationError(
                "Unable to export cache as JSON."
            ) from exc

    # ------------------------------------------------------------------
    # Statistics and health
    # ------------------------------------------------------------------

    def stats_snapshot(self) -> dict[str, Any]:
        with self._lock:
            result = self._stats.snapshot()
            result.update({
                "namespace": self.namespace,
                "entries": len(self._entries),
                "total_size": self._total_size,
                "state": self._state.value,
                "max_entries": self.config.max_entries,
                "max_size": self.config.max_size,
                "default_ttl": self.config.default_ttl,
            })

        return result

    def reset_stats(self) -> None:
        with self._lock:
            self._stats.reset()

    def health(self) -> bool:
        try:
            with self._lock:
                self._ensure_open()
                if self._total_size < 0:
                    return False
                if len(self._entries) < 0:
                    return False
                return True
        except Exception:
            return False

    def info(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "state": self.state.value,
            "size": self.size,
            "total_size": self.total_size,
            "stats": self.stats_snapshot(),
            "health": self.health(),
        }

    # ------------------------------------------------------------------
    # Listener registration
    # ------------------------------------------------------------------

    def add_listener(
        self,
        listener: Callable[[CacheEvent], None],
    ) -> None:
        if not callable(listener):
            raise TypeError(
                "listener must be callable."
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

    def add_eviction_listener(
        self,
        listener: EvictionListener,
    ) -> None:
        if not callable(listener):
            raise TypeError(
                "listener must be callable."
            )

        with self._lock:
            if listener not in self._eviction_listeners:
                self._eviction_listeners.append(
                    listener
                )

    def remove_eviction_listener(
        self,
        listener: EvictionListener,
    ) -> None:
        with self._lock:
            if listener in self._eviction_listeners:
                self._eviction_listeners.remove(
                    listener
                )

    # ------------------------------------------------------------------
    # Tag inspection
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

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Cache[V]":
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "Cache("
            f"namespace={self.namespace!r}, "
            f"size={self.size}, "
            f"state={self.state.value!r})"
        )


# ============================================================================
# Specialized policies
# ============================================================================

class AlwaysAdmit:
    """Admission policy accepting every value."""

    def admit(
        self,
        key: str,
        value: Any,
    ) -> bool:
        return True


class RejectNone:
    """Admission policy rejecting None values."""

    def admit(
        self,
        key: str,
        value: Any,
    ) -> bool:
        return value is not None


class MaximumValueSize:
    """Admission policy rejecting values above a byte estimate."""

    def __init__(
        self,
        maximum: int,
    ) -> None:
        if maximum <= 0:
            raise ValueError(
                "maximum must be positive."
            )

        self.maximum = maximum

    def admit(
        self,
        key: str,
        value: Any,
    ) -> bool:
        return estimate_size(value) <= self.maximum


class CompositeAdmissionPolicy:
    """Combine several admission policies."""

    def __init__(
        self,
        policies: Iterable[AdmissionPolicy],
    ) -> None:
        self.policies = tuple(policies)

    def admit(
        self,
        key: str,
        value: Any,
    ) -> bool:
        return all(
            policy.admit(
                key,
                value,
            )
            for policy in self.policies
        )


# ============================================================================
# Cache decorators
# ============================================================================

def cached(
    cache: Cache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
    tags: Iterable[str] = (),
) -> Callable[
    [Callable[P, T]],
    Callable[P, T],
]:
    """Cache the result of a synchronous function."""

    def decorator(
        function: Callable[P, T],
    ) -> Callable[P, T]:
        @functools.wraps(function)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> T:
            if key_builder is not None:
                key = key_builder(
                    *args,
                    **kwargs,
                )
            else:
                key = _function_cache_key(
                    function,
                    args,
                    kwargs,
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
            )

            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        wrapper.invalidate = lambda *a, **kw: cache.delete(  # type: ignore[attr-defined]
            key_builder(*a, **kw)
            if key_builder is not None
            else _function_cache_key(function, a, kw)
        )

        return wrapper

    return decorator


def async_cached(
    cache: Cache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
    tags: Iterable[str] = (),
) -> Callable[
    [Callable[P, Any]],
    Callable[P, Any],
]:
    """Cache an async function result."""

    def decorator(
        function: Callable[P, Any],
    ) -> Callable[P, Any]:
        @functools.wraps(function)
        async def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Any:
            if key_builder is not None:
                key = key_builder(
                    *args,
                    **kwargs,
                )
            else:
                key = _function_cache_key(
                    function,
                    args,
                    kwargs,
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
            )

            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator


def _function_cache_key(
    function: Callable[..., Any],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
) -> str:
    """Build a stable function-call cache key."""
    try:
        payload = pickle.dumps(
            (
                function.__module__,
                function.__qualname__,
                tuple(args),
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
        ).encode("utf-8")

    return (
        f"{function.__module__}:"
        f"{function.__qualname__}:"
        f"{hashlib.sha256(payload).hexdigest()}"
    )


# ============================================================================
# Module-level cache
# ============================================================================

default_cache = Cache[Any](
    namespace=DEFAULT_NAMESPACE,
)


def get(
    key: Any,
    default: Any = None,
    **kwargs: Any,
) -> Any:
    """Read from the default cache."""
    return default_cache.get(
        key,
        default,
        **kwargs,
    )


def set(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> Any:
    """Write to the default cache."""
    return default_cache.set(
        key,
        value,
        **kwargs,
    )


def add(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Add to the default cache."""
    return default_cache.add(
        key,
        value,
        **kwargs,
    )


def replace(
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Replace in the default cache."""
    return default_cache.replace(
        key,
        value,
        **kwargs,
    )


def delete(
    key: Any,
) -> bool:
    """Delete from the default cache."""
    return default_cache.delete(
        key
    )


def clear() -> int:
    """Clear the default cache."""
    return default_cache.clear()


def exists(
    key: Any,
) -> bool:
    """Check the default cache."""
    return default_cache.contains(
        key
    )


def get_or_set(
    key: Any,
    factory: Callable[[], T],
    **kwargs: Any,
) -> T:
    """Get or compute a value in the default cache."""
    return default_cache.get_or_set(
        key,
        factory,
        **kwargs,
    )


def cache_stats() -> dict[str, Any]:
    """Return default cache statistics."""
    return default_cache.stats_snapshot()


def cache_health() -> bool:
    """Return default cache health."""
    return default_cache.health()


def cache_snapshot() -> CacheSnapshot:
    """Create a snapshot of the default cache."""
    return default_cache.snapshot()


def invalidate_tag(
    tag: str,
) -> int:
    """Invalidate a tag in the default cache."""
    return default_cache.invalidate_tag(
        tag
    )


def cleanup_expired() -> int:
    """Remove expired entries from the default cache."""
    return default_cache.cleanup_expired()


# ============================================================================
# Namespace factory
# ============================================================================

class CacheNamespace(Generic[V]):
    """Scoped view over a Cache instance."""

    def __init__(
        self,
        cache: Cache[V],
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
        prefix = self.namespace + ":"
        return self.cache.invalidate_prefix(
            prefix
        )

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

    def __getitem__(
        self,
        key: Any,
    ) -> Any:
        return self.get(key)

    def __setitem__(
        self,
        key: Any,
        value: V,
    ) -> None:
        self.set(
            key,
            value,
        )

    def __contains__(
        self,
        key: object,
    ) -> bool:
        return self.contains(key)


def namespace(
    name: str,
    *,
    cache: Cache[Any] | None = None,
) -> CacheNamespace[Any]:
    """Create a namespace over a cache."""
    return CacheNamespace(
        cache or default_cache,
        name,
    )


# ============================================================================
# Testing and factory helpers
# ============================================================================

def create_cache(
    *,
    namespace: str = DEFAULT_NAMESPACE,
    default_ttl: float | None = DEFAULT_TTL,
    max_entries: int = DEFAULT_MAX_ENTRIES,
    max_size: int = DEFAULT_MAX_SIZE,
    allow_stale: bool = False,
    copy_values: bool = False,
    negative_ttl: float | None = None,
    lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
    serializer: ValueSerializer | None = None,
    admission_policy: AdmissionPolicy | None = None,
) -> Cache[Any]:
    """Create a configured cache instance."""
    return Cache(
        namespace=namespace,
        default_ttl=default_ttl,
        max_entries=max_entries,
        max_size=max_size,
        allow_stale=allow_stale,
        copy_values=copy_values,
        negative_ttl=negative_ttl,
        lock_timeout=lock_timeout,
        serializer=serializer,
        admission_policy=admission_policy,
    )


def create_isolated_cache(
    **kwargs: Any,
) -> Cache[Any]:
    """Create an isolated cache intended for tests."""
    return Cache(
        namespace=kwargs.pop(
            "namespace",
            "test",
        ),
        default_ttl=kwargs.pop(
            "default_ttl",
            None,
        ),
        max_entries=kwargs.pop(
            "max_entries",
            0,
        ),
        max_size=kwargs.pop(
            "max_size",
            0,
        ),
        **kwargs,
    )


def warm_cache(
    cache: Cache[Any],
    values: Mapping[Any, Any],
    *,
    ttl: float | None = None,
    tags: Iterable[str] = (),
) -> int:
    """Populate a cache from a mapping."""
    return cache.set_many(
        values,
        ttl=ttl,
        tags=tags,
    )


def drain_cache(
    cache: Cache[Any],
) -> dict[str, Any]:
    """Extract all cache values and clear the cache."""
    values = dict(
        cache.items()
    )
    cache.clear()
    return values


# ============================================================================
# Extended utility operations
# ============================================================================

def copy_cache(
    source: Cache[Any],
    destination: Cache[Any],
    *,
    overwrite: bool = True,
) -> int:
    """Copy entries between compatible cache instances."""
    count = 0

    for entry in source.entries(
        include_expired=False
    ):
        if (
            not overwrite
            and destination.contains(entry.key)
        ):
            continue

        ttl = entry.remaining_ttl(
            source._now()
        )

        destination.set(
            entry.key,
            entry.value,
            ttl=ttl,
            tags=entry.tags,
            version=entry.version,
            negative=entry.negative,
        )

        count += 1

    return count


def merge_cache(
    target: Cache[Any],
    sources: Iterable[Cache[Any]],
    *,
    overwrite: bool = True,
) -> int:
    """Merge multiple cache instances into one."""
    count = 0

    for source in sources:
        count += copy_cache(
            source,
            target,
            overwrite=overwrite,
        )

    return count


def cache_digest(
    cache: Cache[Any],
) -> str:
    """Calculate a deterministic digest of cache keys and versions."""
    parts = []

    for entry in sorted(
        cache.entries(
            include_expired=False
        ),
        key=lambda item: item.key,
    ):
        parts.append(
            f"{entry.key}:{entry.version}:{entry.size}"
        )

    return hashlib.sha256(
        "\n".join(parts).encode("utf-8")
    ).hexdigest()


def compare_cache(
    first: Cache[Any],
    second: Cache[Any],
) -> dict[str, Any]:
    """Compare keys and metadata between two caches."""
    first_entries = {
        entry.key: entry
        for entry in first.entries()
    }

    second_entries = {
        entry.key: entry
        for entry in second.entries()
    }

    added = sorted(
        second_entries.keys()
        - first_entries.keys()
    )
    removed = sorted(
        first_entries.keys()
        - second_entries.keys()
    )
    common = (
        first_entries.keys()
        & second_entries.keys()
    )

    changed = []

    for key in sorted(common):
        left = first_entries[key]
        right = second_entries[key]

        if (
            left.version != right.version
            or left.size != right.size
            or left.value != right.value
        ):
            changed.append(key)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "equal": not (
            added
            or removed
            or changed
        ),
    }


# ============================================================================
# Export list
# ============================================================================

__all__ = [
    "DEFAULT_TTL",
    "DEFAULT_MAX_ENTRIES",
    "DEFAULT_MAX_SIZE",
    "DEFAULT_NAMESPACE",
    "DEFAULT_VERSION",
    "DEFAULT_LOCK_TIMEOUT",
    "CacheError",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheCapacityError",
    "CacheFrozenError",
    "CacheClosedError",
    "CacheLockTimeout",
    "CacheVersionError",
    "CacheConfigurationError",
    "CacheEventType",
    "EvictionReason",
    "CacheState",
    "PickleSerializer",
    "JsonSerializer",
    "normalize_namespace",
    "normalize_key",
    "make_key",
    "hash_key",
    "estimate_size",
    "CacheEntry",
    "CacheEvent",
    "CacheStats",
    "CacheSnapshot",
    "CacheConfig",
    "Cache",
    "AlwaysAdmit",
    "RejectNone",
    "MaximumValueSize",
    "CompositeAdmissionPolicy",
    "cached",
    "async_cached",
    "default_cache",
    "get",
    "set",
    "add",
    "replace",
    "delete",
    "clear",
    "exists",
    "get_or_set",
    "cache_stats",
    "cache_health",
    "cache_snapshot",
    "invalidate_tag",
    "cleanup_expired",
    "CacheNamespace",
    "namespace",
    "create_cache",
    "create_isolated_cache",
    "warm_cache",
    "drain_cache",
    "copy_cache",
    "merge_cache",
    "cache_digest",
    "compare_cache",
]