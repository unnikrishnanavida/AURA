from __future__ import annotations

import time
from typing import Any, Dict


class MemoryCache:
    def __init__(self) -> None:
        self._store: Dict[str, tuple[Any, float | None]] = {}

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        expiry = time.time() + ttl if ttl else None
        self._store[key] = (value, expiry)

    def get(self, key: str):
        v = self._store.get(key)
        if not v:
            return None
        value, expiry = v
        if expiry and expiry < time.time():
            del self._store[key]
            return None
        return value
