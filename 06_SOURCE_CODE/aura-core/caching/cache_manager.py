from __future__ import annotations

from typing import Any

from .memory_cache import MemoryCache


class CacheManager:
    def __init__(self) -> None:
        self.memory = MemoryCache()

    def get(self, key: str) -> Any:
        return self.memory.get(key)

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self.memory.set(key, value, ttl)
