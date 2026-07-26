"""Caching utilities for registry lookups."""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class RegistryCache(Generic[K, V]):
    """A bounded in-memory cache suitable for frequently accessed registry records."""

    def __init__(self, max_size: int = 256) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero")
        self.max_size = max_size
        self._store: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> V | None:
        """Return a cached value if present, moving it to the most recently used position."""
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: K, value: V) -> None:
        """Store or update a cached value."""
        self._store.pop(key, None)
        self._store[key] = value
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def delete(self, key: K) -> None:
        """Remove a cached value."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._store.clear()

    def size(self) -> int:
        """Return the current cache size."""
        return len(self._store)

    def items(self) -> list[tuple[K, V]]:
        """Return all cached items from most recent to least recent."""
        return list(self._store.items())
