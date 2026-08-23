from __future__ import annotations

import asyncio
import contextlib
import copy
import functools
import hashlib
import inspect
import json
import os
import pickle
import shutil
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, ParamSpec, TypeVar

try:
    from .cache import (
        Cache,
        CacheClosedError,
        CacheConfigurationError,
        CacheError,
        CacheFrozenError,
        CacheLockTimeout,
        CacheVersionError,
        EvictionReason,
        estimate_size,
        normalize_key,
        normalize_namespace,
    )
except ImportError:
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
    class EvictionReason:
        CAPACITY = "capacity"
        EXPIRED = "expired"
        EXPLICIT = "explicit"
        INVALIDATED = "invalidated"
    def normalize_namespace(value):
        return str(value or "default").strip() or "default"
    def normalize_key(key, *, namespace=None):
        text = str(key).strip()
        if not text:
            raise ValueError("empty key")
        return f"{normalize_namespace(namespace)}:{text}"
    def estimate_size(value):
        try:
            return len(pickle.dumps(value))
        except Exception:
            return len(repr(value))


P = ParamSpec("P")
T = TypeVar("T")
V = TypeVar("V")

DEFAULT_DISK_NAMESPACE = "disk"
DEFAULT_MAX_ENTRIES = 100_000
DEFAULT_MAX_BYTES = 0
DEFAULT_TTL = 86_400.0
DEFAULT_FILE_SUFFIX = ".auracache"
DEFAULT_COMPACTION_INTERVAL = 128
DEFAULT_LOCK_TIMEOUT = 30.0


class DiskCacheError(CacheError):
    """Base disk-cache exception."""


class DiskCorruptionError(DiskCacheError):
    """Raised when a cache record fails integrity validation."""


class DiskCapacityError(DiskCacheError):
    """Raised when disk capacity cannot be satisfied."""


class DiskLockError(DiskCacheError):
    """Raised when a cache lock cannot be acquired."""


class DiskSerializationError(DiskCacheError):
    """Raised when a value cannot be serialized."""


class DiskRecoveryError(DiskCacheError):
    """Raised when a recovery operation fails."""


@dataclass
class DiskCacheConfig:
    """Validated configuration for DiskCache."""

    directory: Path
    namespace: str = DEFAULT_DISK_NAMESPACE
    default_ttl: float | None = DEFAULT_TTL
    max_entries: int = DEFAULT_MAX_ENTRIES
    max_bytes: int = DEFAULT_MAX_BYTES
    file_suffix: str = DEFAULT_FILE_SUFFIX
    fsync: bool = True
    stale_grace: float = 0.0
    allow_stale: bool = False
    copy_values: bool = False
    compaction_interval: int = DEFAULT_COMPACTION_INTERVAL
    lock_timeout: float = DEFAULT_LOCK_TIMEOUT
    compression: bool = False

    def validate(self) -> None:
        if self.default_ttl is not None and self.default_ttl < 0:
            raise DiskCacheError("default_ttl cannot be negative")
        if self.max_entries < 0:
            raise DiskCacheError("max_entries cannot be negative")
        if self.max_bytes < 0:
            raise DiskCacheError("max_bytes cannot be negative")
        if self.stale_grace < 0:
            raise DiskCacheError("stale_grace cannot be negative")
        if self.compaction_interval <= 0:
            raise DiskCacheError("compaction_interval must be positive")
        if self.lock_timeout < 0:
            raise DiskCacheError("lock_timeout cannot be negative")


@dataclass
class DiskRecord(Generic[V]):
    """Serializable disk record."""

    key: str
    value: V
    created_at: float
    accessed_at: float
    expires_at: float | None
    version: int
    size: int
    checksum: str
    tags: tuple[str, ...] = ()
    access_count: int = 0
    stale: bool = False
    protected: bool = False
    generation: int = 0

    def expired(self, now: float) -> bool:
        return (
            self.expires_at is not None
            and now >= self.expires_at
        )

    def stale_now(
        self,
        now: float,
        grace: float,
    ) -> bool:
        return (
            self.expires_at is not None
            and now >= self.expires_at
            and now <= self.expires_at + grace
        )

    def remaining_ttl(self, now: float) -> float | None:
        if self.expires_at is None:
            return None
        return max(0.0, self.expires_at - now)


@dataclass
class DiskStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    adds: int = 0
    replaces: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0
    invalidations: int = 0
    corruptions: int = 0
    quarantined: int = 0
    reads: int = 0
    writes: int = 0
    bytes_read: int = 0
    bytes_written: int = 0
    compactions: int = 0
    maintenance_runs: int = 0
    recovery_runs: int = 0
    recovery_failures: int = 0
    peak_entries: int = 0
    peak_bytes: int = 0

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.requests if self.requests else 0.0

    def snapshot(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data["requests"] = self.requests
        data["hit_rate"] = self.hit_rate
        return data


@dataclass(frozen=True)
class DiskSnapshot:
    namespace: str
    created_at: float
    records: tuple[DiskRecord[Any], ...]
    stats: Mapping[str, Any]


def _checksum_payload(value: Any) -> bytes:
    try:
        return pickle.dumps(
            value,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    except Exception as exc:
        raise DiskSerializationError(
            "Value is not serializable."
        ) from exc


def _checksum(value: Any) -> str:
    return hashlib.sha256(
        _checksum_payload(value)
    ).hexdigest()


def _safe_name(key: str) -> str:
    digest = hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()
    return digest


def _atomic_write(path: Path, payload: bytes, fsync: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            if fsync:
                os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


class DiskCache(Cache[V], Generic[V]):
    """Persistent filesystem-backed cache."""

    def __init__(
        self,
        directory: str | Path,
        *,
        namespace: str = DEFAULT_DISK_NAMESPACE,
        default_ttl: float | None = DEFAULT_TTL,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_bytes: int = DEFAULT_MAX_BYTES,
        fsync: bool = True,
        stale_grace: float = 0.0,
        allow_stale: bool = False,
        copy_values: bool = False,
        compaction_interval: int = DEFAULT_COMPACTION_INTERVAL,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        compression: bool = False,
    ) -> None:
        self.config = DiskCacheConfig(
            directory=Path(directory),
            namespace=normalize_namespace(namespace),
            default_ttl=default_ttl,
            max_entries=max_entries,
            max_bytes=max_bytes,
            fsync=fsync,
            stale_grace=stale_grace,
            allow_stale=allow_stale,
            copy_values=copy_values,
            compaction_interval=compaction_interval,
            lock_timeout=lock_timeout,
            compression=compression,
        )
        self.config.validate()
        self.config.directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._root = (
            self.config.directory
            / self.config.namespace
        )
        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._lock = threading.RLock()
        self._state = "ready"
        self._stats = DiskStats()
        self._generation = 0
        self._operations = 0
        self._index: dict[str, dict[str, Any]] = {}
        self._load_index()

    @property
    def namespace(self) -> str:
        return self.config.namespace

    @property
    def directory(self) -> Path:
        return self._root

    @property
    def state(self) -> str:
        return self._state

    @property
    def stats(self) -> DiskStats:
        return self._stats

    @property
    def max_entries(self) -> int:
        return self.config.max_entries

    @property
    def max_bytes(self) -> int:
        return self.config.max_bytes

    def _ensure_open(self) -> None:
        if self._state == "closed":
            raise CacheClosedError("Disk cache is closed.")

    def _ensure_mutable(self) -> None:
        self._ensure_open()
        if self._state == "frozen":
            raise CacheFrozenError("Disk cache is frozen.")

    def initialize(self) -> None:
        self._ensure_open()
        self._root.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def close(self) -> None:
        with self._lock:
            self._state = "closed"

    def shutdown(self) -> None:
        self.close()

    def freeze(self) -> None:
        self._ensure_open()
        self._state = "frozen"

    def unfreeze(self) -> None:
        self._ensure_open()
        self._state = "ready"

    def reset(self) -> None:
        self._ensure_mutable()
        self.clear()
        self._stats = DiskStats()

    def _key(self, key: Any) -> str:
        return normalize_key(
            key,
            namespace=self.namespace,
        )

    def _path(self, normalized: str) -> Path:
        return (
            self._root
            / (
                _safe_name(normalized)
                + self.config.file_suffix
            )
        )

    def _meta_path(self) -> Path:
        return self._root / "_index.json"

    def _lock_path(self) -> Path:
        return self._root / ".lock"

    def _load_index(self) -> None:
        path = self._meta_path()
        if not path.exists():
            self._index = {}
            return
        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
            self._index = (
                data
                if isinstance(data, dict)
                else {}
            )
        except Exception:
            self._index = {}

    def _save_index(self) -> None:
        payload = json.dumps(
            self._index,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        _atomic_write(
            self._meta_path(),
            payload,
            self.config.fsync,
        )

    def _serialize_record(
        self,
        record: DiskRecord[V],
    ) -> bytes:
        try:
            return pickle.dumps(
                record,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise DiskSerializationError(
                f"Unable to serialize key {record.key!r}."
            ) from exc

    def _deserialize_record(
        self,
        payload: bytes,
    ) -> DiskRecord[V]:
        try:
            record = pickle.loads(payload)
        except Exception as exc:
            raise DiskCorruptionError(
                "Unable to deserialize disk record."
            ) from exc
        if not isinstance(record, DiskRecord):
            raise DiskCorruptionError(
                "Disk record has an invalid type."
            )
        if _checksum(record.value) != record.checksum:
            raise DiskCorruptionError(
                f"Checksum mismatch for {record.key!r}."
            )
        return record

    def _read_record(
        self,
        normalized: str,
    ) -> DiskRecord[V] | None:
        path = self._path(normalized)
        if not path.exists():
            return None
        try:
            payload = path.read_bytes()
            self._stats.reads += 1
            self._stats.bytes_read += len(payload)
            return self._deserialize_record(payload)
        except DiskCorruptionError:
            self._stats.corruptions += 1
            self._quarantine(path)
            return None
        except OSError:
            return None

    def _write_record(
        self,
        record: DiskRecord[V],
    ) -> None:
        payload = self._serialize_record(
            record
        )
        _atomic_write(
            self._path(record.key),
            payload,
            self.config.fsync,
        )
        self._stats.writes += 1
        self._stats.bytes_written += len(payload)
        self._index[record.key] = {
            "size": record.size,
            "accessed_at": record.accessed_at,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
            "version": record.version,
            "tags": list(record.tags),
            "protected": record.protected,
        }
        self._save_index()

    def _quarantine(self, path: Path) -> None:
        if not path.exists():
            return
        target = path.with_name(
            path.name
            + f".corrupt.{int(time.time())}"
        )
        try:
            os.replace(path, target)
            self._stats.quarantined += 1
        except OSError:
            pass

    def _copy_value(self, value: V) -> V:
        if not self.config.copy_values:
            return value
        try:
            return copy.deepcopy(value)
        except Exception:
            return value

    def _expiry(
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
        return time.time() + selected

    def _record_size(
        self,
        value: Any,
    ) -> int:
        return max(
            1,
            len(_checksum_payload(value)),
        )

    def _next_generation(self) -> int:
        self._generation += 1
        return self._generation

    def _records(self) -> list[DiskRecord[Any]]:
        records = []
        for key in self._all_keys():
            record = self._read_record(key)
            if record is not None:
                records.append(record)
        return records

    def _all_keys(self) -> list[str]:
        return [
            key
            for key in self._index.keys()
        ]

    def _remove(
        self,
        normalized: str,
        *,
        reason: str,
    ) -> bool:
        path = self._path(normalized)
        existed = path.exists()
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        self._index.pop(normalized, None)
        self._save_index()
        if existed:
            if reason == "expired":
                self._stats.expirations += 1
            elif reason == "evicted":
                self._stats.evictions += 1
            elif reason == "invalidated":
                self._stats.invalidations += 1
            else:
                self._stats.deletes += 1
        return existed

    def get(
        self,
        key: Any,
        default: Any = None,
        *,
        allow_stale: bool | None = None,
    ) -> Any:
        self._ensure_open()
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                self._stats.misses += 1
                return default

            now = time.time()
            if record.expired(now):
                if (
                    record.stale_now(
                        now,
                        self.config.stale_grace,
                    )
                    and (
                        self.config.allow_stale
                        if allow_stale is None
                        else allow_stale
                    )
                ):
                    record.stale = True
                    record.access_count += 1
                    record.accessed_at = now
                    self._write_record(record)
                    self._stats.hits += 1
                    return self._copy_value(record.value)

                self._remove(
                    normalized,
                    reason="expired",
                )
                self._stats.misses += 1
                return default

            record.access_count += 1
            record.accessed_at = now
            record.stale = False
            self._write_record(record)
            self._stats.hits += 1
            return self._copy_value(record.value)

    def peek(
        self,
        key: Any,
        default: Any = None,
    ) -> Any:
        self._ensure_open()
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                return default
            if record.expired(time.time()):
                return default
            return self._copy_value(record.value)

    def contains(self, key: Any) -> bool:
        marker = object()
        return self.get(key, marker) is not marker

    def exists(self, key: Any) -> bool:
        return self.contains(key)

    def require(self, key: Any) -> V:
        marker = object()
        value = self.get(key, marker)
        if value is marker:
            raise KeyError(self._key(key))
        return value

    def set(
        self,
        key: Any,
        value: V,
        *,
        ttl: float | None = None,
        tags: Iterable[str] = (),
        version: int | None = None,
        protected: bool = False,
    ) -> V:
        self._ensure_mutable()
        normalized = self._key(key)
        prepared = self._copy_value(value)
        now = time.time()

        with self._lock:
            old = self._read_record(normalized)
            selected_version = (
                version
                if version is not None
                else (
                    old.version + 1
                    if old is not None
                    else 1
                )
            )
            record = DiskRecord(
                key=normalized,
                value=prepared,
                created_at=now,
                accessed_at=now,
                expires_at=self._expiry(ttl),
                version=selected_version,
                size=self._record_size(prepared),
                checksum=_checksum(prepared),
                tags=tuple(
                    sorted(
                        {
                            str(tag).strip()
                            for tag in tags
                            if str(tag).strip()
                        }
                    )
                ),
                access_count=0,
                stale=False,
                protected=protected,
                generation=self._next_generation(),
            )
            self._write_record(record)
            self._stats.sets += 1
            self._operations += 1
            self._enforce_capacity()
            if (
                self._operations
                % self.config.compaction_interval
                == 0
            ):
                self.compact()
        return self._copy_value(prepared)

    def add(
        self,
        key: Any,
        value: V,
        **kwargs: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is not None and not record.expired(time.time()):
                return False
            if record is not None:
                self._remove(
                    normalized,
                    reason="expired",
                )
        self.set(normalized, value, **kwargs)
        self._stats.adds += 1
        return True

    def replace(
        self,
        key: Any,
        value: V,
        **kwargs: Any,
    ) -> bool:
        self._ensure_mutable()
        normalized = self._key(key)
        if not self.contains(normalized):
            return False
        self.set(normalized, value, **kwargs)
        self._stats.replaces += 1
        return True

    def delete(self, key: Any) -> bool:
        self._ensure_mutable()
        return self._remove(
            self._key(key),
            reason="explicit",
        )

    def pop(
        self,
        key: Any,
        default: Any = None,
    ) -> Any:
        self._ensure_mutable()
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                return default
            self._remove(
                normalized,
                reason="explicit",
            )
            return self._copy_value(record.value)

    def get_many(
        self,
        keys: Iterable[Any],
        *,
        include_missing: bool = False,
    ) -> dict[str, Any]:
        result = {}
        marker = object()
        for key in keys:
            normalized = self._key(key)
            value = self.get(
                normalized,
                marker,
            )
            if value is marker:
                if include_missing:
                    result[normalized] = None
            else:
                result[normalized] = value
        return result

    def set_many(
        self,
        values: Mapping[Any, V],
        **kwargs: Any,
    ) -> int:
        count = 0
        for key, value in values.items():
            self.set(key, value, **kwargs)
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

    def ttl(self, key: Any) -> float | None:
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                return None
            return record.remaining_ttl(time.time())

    def expire(self, key: Any, ttl: float) -> bool:
        self._ensure_mutable()
        if ttl < 0:
            raise CacheConfigurationError(
                "TTL cannot be negative."
            )
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                return False
            record.expires_at = time.time() + ttl
            record.stale = False
            self._write_record(record)
            return True

    def persist(self, key: Any) -> bool:
        self._ensure_mutable()
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None:
                return False
            record.expires_at = None
            record.stale = False
            self._write_record(record)
            return True

    def version(self, key: Any) -> int | None:
        normalized = self._key(key)
        with self._lock:
            record = self._read_record(normalized)
            if record is None or record.expired(time.time()):
                return None
            return record.version

    def compare_and_set(
        self,
        key: Any,
        expected_version: int | None,
        value: V,
        **kwargs: Any,
    ) -> int:
        normalized = self._key(key)
        current = self.version(normalized)
        if current != expected_version:
            raise CacheVersionError(
                f"Version mismatch: expected={expected_version!r}, "
                f"actual={current!r}"
            )
        next_version = 1 if current is None else current + 1
        self.set(
            normalized,
            value,
            version=next_version,
            **kwargs,
        )
        return next_version

    def tags(self) -> list[str]:
        tags = set()
        for record in self._records():
            tags.update(record.tags)
        return sorted(tags)

    def keys_for_tag(self, tag: str) -> list[str]:
        normalized = str(tag).strip()
        return sorted(
            record.key
            for record in self._records()
            if normalized in record.tags
        )

    def invalidate_tag(self, tag: str) -> int:
        keys = self.keys_for_tag(tag)
        return self.delete_many(keys)

    def keys(self) -> list[str]:
        self.cleanup_expired()
        return self._all_keys()

    def values(self) -> list[V]:
        return [
            self.get(key)
            for key in self.keys()
        ]

    def items(self) -> list[tuple[str, V]]:
        return [
            (key, self.get(key))
            for key in self.keys()
        ]

    def __len__(self) -> int:
        return len(self._all_keys())

    def __contains__(self, key: object) -> bool:
        try:
            return self.contains(key)
        except Exception:
            return False

    def __getitem__(self, key: Any) -> Any:
        return self.require(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.set(key, value)

    def _enforce_capacity(self) -> int:
        records = self._records()
        removed = 0

        def total_bytes() -> int:
            return sum(r.size for r in records)

        while (
            self.max_entries > 0
            and len(records) > self.max_entries
        ) or (
            self.max_bytes > 0
            and total_bytes() > self.max_bytes
        ):
            candidates = [
                r for r in records
                if not r.protected
            ]
            if not candidates:
                raise DiskCapacityError(
                    "Capacity cannot be satisfied because all "
                    "records are protected."
                )
            candidate = min(
                candidates,
                key=lambda r: (
                    r.accessed_at,
                    r.access_count,
                    r.created_at,
                ),
            )
            self._remove(
                candidate.key,
                reason="evicted",
            )
            records = [
                r for r in records
                if r.key != candidate.key
            ]
            removed += 1

        self._stats.peak_entries = max(
            self._stats.peak_entries,
            len(records),
        )
        self._stats.peak_bytes = max(
            self._stats.peak_bytes,
            total_bytes(),
        )
        return removed

    def cleanup_expired(self) -> int:
        self._ensure_mutable()
        removed = 0
        now = time.time()
        for record in self._records():
            if record.expired(now):
                if self._remove(
                    record.key,
                    reason="expired",
                ):
                    removed += 1
        self._stats.maintenance_runs += 1
        return removed

    def compact(self) -> dict[str, int]:
        self._ensure_mutable()
        before = len(self._all_keys())
        expired = self.cleanup_expired()
        evicted = self._enforce_capacity()
        self._stats.compactions += 1
        return {
            "before": before,
            "expired": expired,
            "evicted": evicted,
            "after": len(self._all_keys()),
        }

    def clear(self) -> int:
        self._ensure_mutable()
        keys = self._all_keys()
        for key in keys:
            self._remove(
                key,
                reason="explicit",
            )
        self._stats.deletes += 0
        return len(keys)

    def snapshot(self) -> DiskSnapshot:
        return DiskSnapshot(
            namespace=self.namespace,
            created_at=time.time(),
            records=tuple(
                copy.deepcopy(
                    self._records()
                )
            ),
            stats=self._stats.snapshot(),
        )

    def restore(
        self,
        snapshot: DiskSnapshot,
        *,
        clear_first: bool = True,
    ) -> int:
        self._ensure_mutable()
        if snapshot.namespace != self.namespace:
            raise DiskRecoveryError(
                "Snapshot namespace does not match."
            )
        if clear_first:
            self.clear()
        count = 0
        now = time.time()
        for record in snapshot.records:
            if record.expired(now):
                continue
            self._write_record(
                copy.deepcopy(record)
            )
            count += 1
        self._enforce_capacity()
        return count

    def export_bytes(self) -> bytes:
        try:
            return pickle.dumps(
                self.snapshot(),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise DiskSerializationError(
                "Unable to export snapshot."
            ) from exc

    def import_bytes(
        self,
        payload: bytes,
        *,
        clear_first: bool = True,
    ) -> int:
        try:
            snapshot = pickle.loads(payload)
        except Exception as exc:
            raise DiskRecoveryError(
                "Invalid snapshot payload."
            ) from exc
        if not isinstance(snapshot, DiskSnapshot):
            raise DiskRecoveryError(
                "Snapshot has an invalid type."
            )
        return self.restore(
            snapshot,
            clear_first=clear_first,
        )

    def backup(self, destination: str | Path) -> Path:
        self._ensure_open()
        target = Path(destination)
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(
            self._root,
            target,
        )
        return target

    def recover(self, source: str | Path) -> int:
        self._ensure_mutable()
        source_path = Path(source)
        if not source_path.exists():
            raise DiskRecoveryError(
                f"Recovery source does not exist: {source_path}"
            )
        self.clear()
        count = 0
        for path in source_path.glob(
            f"*{self.config.file_suffix}"
        ):
            target = self._root / path.name
            shutil.copy2(
                path,
                target,
            )
            count += 1
        self._load_index()
        self._stats.recovery_runs += 1
        return count

    def validate(self) -> dict[str, Any]:
        checked = 0
        valid = 0
        invalid = []
        for key in self._all_keys():
            checked += 1
            record = self._read_record(key)
            if record is None:
                invalid.append(key)
            else:
                valid += 1
        return {
            "checked": checked,
            "valid": valid,
            "invalid": invalid,
            "health": not invalid,
        }

    def stats_snapshot(self) -> dict[str, Any]:
        data = self._stats.snapshot()
        data.update({
            "namespace": self.namespace,
            "directory": str(self.directory),
            "entries": len(self._all_keys()),
            "state": self.state,
            "max_entries": self.max_entries,
            "max_bytes": self.max_bytes,
        })
        return data

    def health(self) -> bool:
        try:
            result = self.validate()
            return bool(result["health"])
        except Exception:
            return False

    def diagnose(self) -> dict[str, Any]:
        return {
            "health": self.health(),
            "stats": self.stats_snapshot(),
            "validation": self.validate(),
            "directory": str(self.directory),
        }

    def warm(
        self,
        values: Mapping[Any, V],
        **kwargs: Any,
    ) -> int:
        count = 0
        for key, value in values.items():
            self.set(key, value, **kwargs)
            count += 1
        return count

    def get_or_set(
        self,
        key: Any,
        factory: Callable[[], V],
        **kwargs: Any,
    ) -> V:
        marker = object()
        value = self.get(key, marker)
        if value is not marker:
            return value
        result = factory()
        self.set(key, result, **kwargs)
        return result

    async def aget_or_set(
        self,
        key: Any,
        factory: Callable[[], Any],
        **kwargs: Any,
    ) -> Any:
        marker = object()
        value = self.get(key, marker)
        if value is not marker:
            return value
        result = factory()
        if inspect.isawaitable(result):
            result = await result
        self.set(key, result, **kwargs)
        return result

    def scoped(
        self,
        namespace: str,
    ) -> "DiskCacheNamespace":
        return DiskCacheNamespace(
            self,
            namespace,
        )

    def __enter__(self) -> "DiskCache[V]":
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc: Any,
        tb: Any,
    ) -> None:
        self.close()


class DiskCacheNamespace(Generic[V]):
    """Namespace view over a DiskCache."""

    def __init__(
        self,
        cache: DiskCache[V],
        namespace: str,
    ) -> None:
        self.cache = cache
        self.namespace = normalize_namespace(namespace)

    def key(self, key: Any) -> str:
        return normalize_key(
            key,
            namespace=self.namespace,
        )

    def get(self, key: Any, default: Any = None, **kwargs: Any) -> Any:
        return self.cache.get(
            self.key(key),
            default,
            **kwargs,
        )

    def set(self, key: Any, value: V, **kwargs: Any) -> V:
        return self.cache.set(
            self.key(key),
            value,
            **kwargs,
        )

    def add(self, key: Any, value: V, **kwargs: Any) -> bool:
        return self.cache.add(
            self.key(key),
            value,
            **kwargs,
        )

    def replace(self, key: Any, value: V, **kwargs: Any) -> bool:
        return self.cache.replace(
            self.key(key),
            value,
            **kwargs,
        )

    def delete(self, key: Any) -> bool:
        return self.cache.delete(
            self.key(key)
        )

    def contains(self, key: Any) -> bool:
        return self.cache.contains(
            self.key(key)
        )

    def get_or_set(self, key: Any, factory: Callable[[], V], **kwargs: Any) -> V:
        return self.cache.get_or_set(
            self.key(key),
            factory,
            **kwargs,
        )

    def clear(self) -> int:
        return self.cache.invalidate_prefix(
            self.namespace + ":"
        )

    def keys(self) -> list[str]:
        prefix = self.namespace + ":"
        return [
            key[len(prefix):]
            for key in self.cache.keys()
            if key.startswith(prefix)
        ]


def disk_cached(
    cache: DiskCache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for synchronous disk-backed caching."""
    def decorator(
        function: Callable[P, T],
    ) -> Callable[P, T]:
        @functools.wraps(function)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> T:
            if key_builder:
                key = key_builder(
                    *args,
                    **kwargs,
                )
            else:
                key = (
                    f"{function.__module__}."
                    f"{function.__qualname__}:"
                    f"{hashlib.sha256(repr((args, kwargs)).encode()).hexdigest()}"
                )
            marker = object()
            value = cache.get(key, marker)
            if value is not marker:
                return value
            result = function(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def disk_async_cached(
    cache: DiskCache[Any],
    *,
    key_builder: Callable[..., Any] | None = None,
    ttl: float | None = None,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Decorator for asynchronous disk-backed caching."""
    def decorator(
        function: Callable[P, Any],
    ) -> Callable[P, Any]:
        @functools.wraps(function)
        async def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Any:
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = (
                    f"{function.__module__}."
                    f"{function.__qualname__}:"
                    f"{hashlib.sha256(repr((args, kwargs)).encode()).hexdigest()}"
                )
            marker = object()
            value = cache.get(key, marker)
            if value is not marker:
                return value
            result = function(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            cache.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def create_disk_cache(
    directory: str | Path,
    **kwargs: Any,
) -> DiskCache[Any]:
    """Factory for DiskCache."""
    return DiskCache(
        directory,
        **kwargs,
    )


def open_disk_cache(
    directory: str | Path,
    **kwargs: Any,
) -> DiskCache[Any]:
    """Alias for create_disk_cache."""
    return create_disk_cache(
        directory,
        **kwargs,
    )


def migrate_mapping(
    source: Mapping[Any, V],
    cache: DiskCache[V],
    **kwargs: Any,
) -> int:
    return cache.warm(
        source,
        **kwargs,
    )


def cache_directory_size(
    cache: DiskCache[Any],
) -> int:
    total = 0
    for path in cache.directory.glob("*"):
        if path.is_file():
            with contextlib.suppress(OSError):
                total += path.stat().st_size
    return total


def cache_fingerprint(
    cache: DiskCache[Any],
) -> str:
    records = []
    for record in sorted(
        cache._records(),
        key=lambda item: item.key,
    ):
        records.append(
            f"{record.key}|{record.version}|{record.checksum}"
        )
    return hashlib.sha256(
        "\n".join(records).encode()
    ).hexdigest()


default_disk_cache: DiskCache[Any] | None = None


def configure_default_disk_cache(
    directory: str | Path,
    **kwargs: Any,
) -> DiskCache[Any]:
    global default_disk_cache
    default_disk_cache = create_disk_cache(
        directory,
        **kwargs,
    )
    return default_disk_cache


def _default() -> DiskCache[Any]:
    if default_disk_cache is None:
        raise DiskCacheError(
            "Default disk cache is not configured."
        )
    return default_disk_cache


def get(key: Any, default: Any = None, **kwargs: Any) -> Any:
    return _default().get(
        key,
        default,
        **kwargs,
    )


def set(key: Any, value: Any, **kwargs: Any) -> Any:
    return _default().set(
        key,
        value,
        **kwargs,
    )


def delete(key: Any) -> bool:
    return _default().delete(key)


def clear() -> int:
    return _default().clear()


def stats() -> dict[str, Any]:
    return _default().stats_snapshot()


def health() -> bool:
    return _default().health()


def cleanup() -> int:
    return _default().cleanup_expired()


__all__ = [
    "DEFAULT_DISK_NAMESPACE",
    "DEFAULT_MAX_ENTRIES",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_TTL",
    "DiskCacheError",
    "DiskCorruptionError",
    "DiskCapacityError",
    "DiskLockError",
    "DiskSerializationError",
    "DiskRecoveryError",
    "DiskCacheConfig",
    "DiskRecord",
    "DiskStats",
    "DiskSnapshot",
    "DiskCache",
    "DiskCacheNamespace",
    "disk_cached",
    "disk_async_cached",
    "create_disk_cache",
    "open_disk_cache",
    "migrate_mapping",
    "cache_directory_size",
    "cache_fingerprint",
    "default_disk_cache",
    "configure_default_disk_cache",
    "get",
    "set",
    "delete",
    "clear",
    "stats",
    "health",
    "cleanup",
]