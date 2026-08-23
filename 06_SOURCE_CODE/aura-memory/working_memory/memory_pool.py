"""AURA Memory working_memory memory pool implementation."""

from __future__ import annotations

import asyncio
import logging
import sys
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class _Entry:
    value: Any
    created_at: float
    last_access: float
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl


class MemoryPool:
    """Thread-safe LRU memory pool with TTL and async wrappers.

    Responsibilities
    - Store arbitrary Python objects keyed by string.
    - Maintain an LRU eviction policy when `max_items` is reached.
    - Support per-item TTL (time-to-live) and background expiration.
    - Offer synchronous and async `get`/`put`/`delete` APIs.
    - Provide hooks for metrics and eviction callbacks.

    Complexity
    - get/put/delete: amortized O(1) using OrderedDict for LRU behavior.

    Example
        pool = MemoryPool(max_items=1000, janitor_interval=10.0)
        pool.put('k1', {'foo': 'bar'}, ttl=60)
        v = pool.get('k1')
        await pool.get_async('k1')
    """

    def __init__(
        self,
        max_items: int = 1000,
        default_ttl: Optional[float] = None,
        janitor_interval: float = 5.0,
        eviction_callback: Optional[Callable[[str, Any], None]] = None,
        metrics_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
        self._max_items = max(1, int(max_items))
        self._default_ttl = default_ttl
        self._store: "OrderedDict[str, _Entry]" = OrderedDict()
        self._lock = threading.RLock()
        self._eviction_callback = eviction_callback
        self._metrics_callback = metrics_callback

        # background janitor
        self._janitor_interval = float(janitor_interval)
        self._stop_event = threading.Event()
        self._janitor_thread = threading.Thread(target=self._janitor_loop, daemon=True, name="memory_pool_janitor")
        self._janitor_thread.start()

    # -- Context / lifecycle -------------------------------------------------
    def close(self) -> None:
        """Stop background janitor and clear resources."""
        self._stop_event.set()
        if self._janitor_thread.is_alive():
            self._janitor_thread.join(timeout=2.0)

    # -- Core operations -----------------------------------------------------
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Insert or update a value in the pool.

        Args:
            key: Unique string key.
            value: Arbitrary Python object to store.
            ttl: Optional time-to-live in seconds. If None uses pool default.
        """
        if not key:
            raise ValueError("key must be non-empty")

        with self._lock:
            now = time.time()
            entry_ttl = self._default_ttl if ttl is None else ttl
            if key in self._store:
                # update existing entry and move to end (most recently used)
                self._store.pop(key)
            self._store[key] = _Entry(value=value, created_at=now, last_access=now, ttl=entry_ttl)
            # Evict if necessary
            while len(self._store) > self._max_items:
                evicted_key, evicted_entry = self._store.popitem(last=False)
                logger.debug("Evicted key %s due to capacity", evicted_key)
                try:
                    if self._eviction_callback:
                        self._eviction_callback(evicted_key, evicted_entry.value)
                except Exception:
                    logger.exception("Eviction callback raised for %s", evicted_key)
            self._emit_metric("put", {"key": key, "size": len(self._store)})

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value and mark it as recently used.

        Returns `default` if not present or expired.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._emit_metric("miss", {"key": key})
                return default
            if entry.is_expired():
                # remove expired
                self._store.pop(key, None)
                self._emit_metric("expire", {"key": key})
                try:
                    if self._eviction_callback:
                        self._eviction_callback(key, entry.value)
                except Exception:
                    logger.exception("Eviction callback raised for expired %s", key)
                return default
            # refresh recency
            entry.last_access = time.time()
            # move to end
            self._store.pop(key)
            self._store[key] = entry
            self._emit_metric("hit", {"key": key})
            return entry.value

    def delete(self, key: str) -> bool:
        """Remove a key from the pool. Returns True if removed."""
        with self._lock:
            removed = self._store.pop(key, None) is not None
            if removed:
                self._emit_metric("delete", {"key": key, "size": len(self._store)})
            return removed

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._emit_metric("clear", {})

    # -- Async wrappers -----------------------------------------------------
    async def put_async(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.put, key, value, ttl)

    async def get_async(self, key: str, default: Any = None) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get, key, default)

    async def delete_async(self, key: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.delete, key)

    # -- Internals ----------------------------------------------------------
    def _janitor_loop(self) -> None:
        try:
            while not self._stop_event.wait(self._janitor_interval):
                self._expire_items()
        except Exception:
            logger.exception("Janitor thread failed")

    def _expire_items(self) -> None:
        expired: List[Tuple[str, _Entry]] = []
        with self._lock:
            now = time.time()
            # Collect expired keys without modifying during iteration
            for k, e in list(self._store.items()):
                if e.ttl is not None and (now - e.created_at) > e.ttl:
                    expired.append((k, e))
            for k, _ in expired:
                self._store.pop(k, None)
        for k, e in expired:
            logger.debug("Expired key %s", k)
            try:
                if self._eviction_callback:
                    self._eviction_callback(k, e.value)
            except Exception:
                logger.exception("Eviction callback raised for expired %s", k)
        if expired:
            self._emit_metric("expired_batch", {"count": len(expired)})

    def _emit_metric(self, name: str, payload: Dict[str, Any]) -> None:
        if self._metrics_callback:
            try:
                self._metrics_callback(name, {**payload, "pool_size": len(self._store)})
            except Exception:
                logger.debug("Metrics callback raised for %s", name)

    # -- Health & info ------------------------------------------------------
    def health_check(self) -> bool:
        return self._janitor_thread.is_alive()

    def info(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module": __name__,
                "class": self.__class__.__name__,
                "timestamp": time.time(),
                "size": len(self._store),
                "max_items": self._max_items,
            }

    def describe(self) -> Dict[str, str]:
        return {"package": "working_memory", "module": "memory_pool"}


__all__ = ["MemoryPool"]
