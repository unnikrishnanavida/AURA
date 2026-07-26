"""Caching utilities for the storage subsystem."""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class StorageCache(Generic[K, V]):
    """Small in-memory cache with LRU behaviour."""

    def __init__(self, max_size: int = 128) -> None:
        self.max_size = max_size
        self._store: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> V | None:
        """Return a cached value if present."""
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: K, value: V) -> None:
        """Store a value in the cache."""
        self._store.pop(key, None)
        self._store[key] = value
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)
