"""
AURA Foundation - Caching Package.

Public package surface for AURA's caching subsystem.

The package exposes three complementary implementation layers:

``cache``
    Shared cache contracts, primitives, exceptions, entry models, and
    common utility functions.

``memory_cache``
    Fast process-local storage with TTL, capacity management, tags,
    snapshots, versioning, and single-flight computation.

``disk_cache``
    Durable local filesystem storage with atomic writes, integrity checks,
    snapshots, backups, recovery, and maintenance.

``policy``
    Storage-independent decision logic for admission, TTL, refresh,
    staleness, namespaces, size, and eviction scoring.

This module intentionally keeps import-time behavior predictable. It does
not automatically instantiate disk caches, touch the filesystem, or perform
network operations. Applications can import the package and then explicitly
construct the cache implementation they need.

The long-form helper functions below provide a stable convenience surface
for callers that do not want to depend on a concrete cache class.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Callable

from .cache import *
from .memory_cache import *
from .disk_cache import *
from .policy import *

PACKAGE_NAME = "aura.foundation.caching"
PACKAGE_VERSION = "1.0.0"
SUPPORTED_BACKENDS = (
    "memory",
    "disk",
)
DEFAULT_MEMORY_NAMESPACE = "memory"
DEFAULT_DISK_NAMESPACE = "disk"


def package_info() -> dict[str, Any]:
    """Return package metadata useful for diagnostics."""
    return {
        "name": PACKAGE_NAME,
        "version": PACKAGE_VERSION,
        "backends": SUPPORTED_BACKENDS,
    }


def backend_names() -> tuple[str, ...]:
    """Return supported cache backend names."""
    return SUPPORTED_BACKENDS


def create(
    backend: str = "memory",
    **kwargs: Any,
) -> Any:
    """Create a cache backend by name."""
    normalized = str(
        backend
    ).strip().lower()

    if normalized in (
        "memory",
        "mem",
        "ram",
    ):
        return MemoryCache(
            **kwargs
        )

    if normalized in (
        "disk",
        "filesystem",
        "file",
        "persistent",
    ):
        directory = kwargs.pop(
            "directory",
            kwargs.pop(
                "path",
                None,
            ),
        )

        if directory is None:
            raise ValueError(
                "disk backend requires 'directory'"
            )

        return DiskCache(
            directory,
            **kwargs,
        )

    raise ValueError(
        f"Unsupported cache backend: {backend!r}"
    )


def create_memory(
    **kwargs: Any,
) -> MemoryCache[Any]:
    """Create a memory cache."""
    return MemoryCache(
        **kwargs
    )


def create_disk(
    directory: str | Path,
    **kwargs: Any,
) -> DiskCache[Any]:
    """Create a disk cache."""
    return DiskCache(
        directory,
        **kwargs,
    )


def create_policy_engine(
    policy: Any = None,
) -> PolicyEngine:
    """Create a policy engine."""
    return PolicyEngine(
        policy
    )


def make_context(
    key: str,
    *,
    value: Any = None,
    namespace: str = "default",
    size: int = 0,
    ttl: float | None = None,
    remaining_ttl: float | None = None,
    age: float = 0.0,
    access_count: int = 0,
    hit_count: int = 0,
    miss_count: int = 0,
    tags: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> CachePolicyContext:
    """Build a policy context from ordinary application data."""
    return build_context(
        key,
        value=value,
        namespace=namespace,
        size=size,
        ttl=ttl,
        remaining_ttl=remaining_ttl,
        age=age,
        access_count=access_count,
        hit_count=hit_count,
        miss_count=miss_count,
        tags=tags,
        metadata=metadata,
    )


def cacheable(
    cache: Any,
    *,
    ttl: float | None = None,
    tags: Iterable[str] = (),
    key_builder: Callable[..., Any] | None = None,
):
    """Return the appropriate caching decorator for a backend."""
    if isinstance(
        cache,
        DiskCache,
    ):
        return disk_cached(
            cache,
            ttl=ttl,
            key_builder=key_builder,
        )

    return memory_cached(
        cache,
        ttl=ttl,
        tags=tags,
        key_builder=key_builder,
    )


def clear_cache(
    cache: Any,
) -> int:
    """Clear any compatible cache implementation."""
    clear_method = getattr(
        cache,
        "clear",
        None,
    )
    if not callable(clear_method):
        raise TypeError(
            "cache does not expose clear()"
        )
    return int(
        clear_method()
    )


def cache_health(
    cache: Any,
) -> bool:
    """Return backend health status."""
    method = getattr(
        cache,
        "health",
        None,
    )
    if not callable(method):
        return True
    try:
        return bool(
            method()
        )
    except Exception:
        return False


def cache_stats(
    cache: Any,
) -> dict[str, Any]:
    """Return normalized cache statistics."""
    method = getattr(
        cache,
        "stats_snapshot",
        None,
    )

    if callable(method):
        result = method()
        return (
            dict(result)
            if isinstance(result, Mapping)
            else {"value": result}
        )

    stats = getattr(
        cache,
        "stats",
        None,
    )

    if stats is None:
        return {}

    if isinstance(stats, Mapping):
        return dict(stats)

    snapshot = getattr(
        stats,
        "snapshot",
        None,
    )

    if callable(snapshot):
        result = snapshot()
        return dict(result)

    return {
        name: value
        for name, value in vars(stats).items()
        if not name.startswith("_")
    }


def cache_snapshot(
    cache: Any,
) -> Any:
    """Create a backend snapshot."""
    method = getattr(
        cache,
        "snapshot",
        None,
    )
    if not callable(method):
        raise TypeError(
            "cache does not support snapshots"
        )
    return method()


def restore_snapshot(
    cache: Any,
    snapshot: Any,
    *,
    clear_first: bool = True,
) -> int:
    """Restore a snapshot into a compatible cache."""
    method = getattr(
        cache,
        "restore",
        None,
    )
    if not callable(method):
        raise TypeError(
            "cache does not support restore()"
        )
    return int(
        method(
            snapshot,
            clear_first=clear_first,
        )
    )


def cache_get(
    cache: Any,
    key: Any,
    default: Any = None,
) -> Any:
    """Compatibility helper for cache.get()."""
    return cache.get(
        key,
        default,
    )


def cache_set(
    cache: Any,
    key: Any,
    value: Any,
    **kwargs: Any,
) -> Any:
    """Compatibility helper for cache.set()."""
    return cache.set(
        key,
        value,
        **kwargs,
    )


def cache_add(
    cache: Any,
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Compatibility helper for cache.add()."""
    return bool(
        cache.add(
            key,
            value,
            **kwargs,
        )
    )


def cache_replace(
    cache: Any,
    key: Any,
    value: Any,
    **kwargs: Any,
) -> bool:
    """Compatibility helper for cache.replace()."""
    return bool(
        cache.replace(
            key,
            value,
            **kwargs,
        )
    )


def cache_delete(
    cache: Any,
    key: Any,
) -> bool:
    """Compatibility helper for cache.delete()."""
    return bool(
        cache.delete(key)
    )


def cache_contains(
    cache: Any,
    key: Any,
) -> bool:
    """Compatibility helper for cache.contains()."""
    return bool(
        cache.contains(key)
    )


def cache_get_or_set(
    cache: Any,
    key: Any,
    factory: Callable[[], Any],
    **kwargs: Any,
) -> Any:
    """Compatibility helper for cache.get_or_set()."""
    return cache.get_or_set(
        key,
        factory,
        **kwargs,
    )


def cache_ttl(
    cache: Any,
    key: Any,
) -> float | None:
    """Compatibility helper for TTL inspection."""
    return cache.ttl(key)


def cache_expire(
    cache: Any,
    key: Any,
    ttl: float,
) -> bool:
    """Compatibility helper for TTL assignment."""
    return bool(
        cache.expire(
            key,
            ttl,
        )
    )


def cache_persist(
    cache: Any,
    key: Any,
) -> bool:
    """Compatibility helper for removing TTL."""
    return bool(
        cache.persist(key)
    )


def cache_keys(
    cache: Any,
) -> list[str]:
    """Return cache keys."""
    return list(
        cache.keys()
    )


def cache_items(
    cache: Any,
) -> list[tuple[str, Any]]:
    """Return cache items."""
    return list(
        cache.items()
    )


def cache_warm(
    cache: Any,
    values: Mapping[Any, Any],
    **kwargs: Any,
) -> int:
    """Warm a compatible cache."""
    warm = getattr(
        cache,
        "warm",
        None,
    )
    if callable(warm):
        return int(
            warm(
                values,
                **kwargs,
            )
        )

    count = 0
    for key, value in values.items():
        cache.set(
            key,
            value,
            **kwargs,
        )
        count += 1
    return count


def cache_cleanup(
    cache: Any,
) -> int:
    """Run expiration cleanup when supported."""
    method = getattr(
        cache,
        "cleanup_expired",
        None,
    )
    if callable(method):
        return int(
            method()
        )

    method = getattr(
        cache,
        "cleanup",
        None,
    )
    if callable(method):
        return int(
            method()
        )

    return 0


def cache_maintenance(
    cache: Any,
) -> Any:
    """Run backend maintenance when supported."""
    method = getattr(
        cache,
        "maintenance",
        None,
    )
    if callable(method):
        return method()

    return {
        "expired_removed": cache_cleanup(
            cache
        ),
    }


def cache_namespace(
    cache: Any,
    namespace: str,
) -> Any:
    """Create a namespace-scoped cache view."""
    method = getattr(
        cache,
        "scoped",
        None,
    )
    if not callable(method):
        raise TypeError(
            "cache does not support namespaces"
        )
    return method(
        namespace
    )


def invalidate_tag(
    cache: Any,
    tag: str,
) -> int:
    """Invalidate entries carrying a tag."""
    method = getattr(
        cache,
        "invalidate_tag",
        None,
    )
    if not callable(method):
        raise TypeError(
            "cache does not support tags"
        )
    return int(
        method(tag)
    )


def cache_version(
    cache: Any,
    key: Any,
) -> int | None:
    """Return the current cache-entry version."""
    return cache.version(key)


def compare_and_set(
    cache: Any,
    key: Any,
    expected_version: int | None,
    value: Any,
    **kwargs: Any,
) -> int:
    """Perform a version-aware update."""
    return int(
        cache.compare_and_set(
            key,
            expected_version,
            value,
            **kwargs,
        )
    )


def freeze(
    cache: Any,
) -> None:
    """Freeze a cache against mutation."""
    cache.freeze()


def unfreeze(
    cache: Any,
) -> None:
    """Resume cache mutation."""
    cache.unfreeze()


def close(
    cache: Any,
) -> None:
    """Close a cache."""
    cache.close()


def reset(
    cache: Any,
) -> None:
    """Reset a cache."""
    cache.reset()


def backend_capabilities(
    cache: Any,
) -> dict[str, bool]:
    """Inspect optional capabilities exposed by a backend."""
    names = (
        "get",
        "set",
        "add",
        "replace",
        "delete",
        "get_many",
        "set_many",
        "delete_many",
        "ttl",
        "expire",
        "persist",
        "snapshot",
        "restore",
        "health",
        "warm",
        "get_or_set",
        "compare_and_set",
        "invalidate_tag",
        "scoped",
        "freeze",
        "unfreeze",
        "close",
    )

    return {
        name: callable(
            getattr(
                cache,
                name,
                None,
            )
        )
        for name in names
    }


def describe_backend(
    cache: Any,
) -> dict[str, Any]:
    """Return a portable backend description."""
    return {
        "type": type(cache).__name__,
        "module": type(cache).__module__,
        "namespace": getattr(
            cache,
            "namespace",
            None,
        ),
        "state": getattr(
            cache,
            "state",
            None,
        ),
        "size": getattr(
            cache,
            "size",
            None,
        ),
        "total_bytes": getattr(
            cache,
            "total_bytes",
            None,
        ),
        "capabilities": backend_capabilities(
            cache
        ),
    }


__all__ = [
    "PACKAGE_NAME",
    "PACKAGE_VERSION",
    "SUPPORTED_BACKENDS",
    "package_info",
    "backend_names",
    "create",
    "create_memory",
    "create_disk",
    "create_policy_engine",
    "make_context",
    "cacheable",
    "clear_cache",
    "cache_health",
    "cache_stats",
    "cache_snapshot",
    "restore_snapshot",
    "cache_get",
    "cache_set",
    "cache_add",
    "cache_replace",
    "cache_delete",
    "cache_contains",
    "cache_get_or_set",
    "cache_ttl",
    "cache_expire",
    "cache_persist",
    "cache_keys",
    "cache_items",
    "cache_warm",
    "cache_cleanup",
    "cache_maintenance",
    "cache_namespace",
    "invalidate_tag",
    "cache_version",
    "compare_and_set",
    "freeze",
    "unfreeze",
    "close",
    "reset",
    "backend_capabilities",
    "describe_backend",
]