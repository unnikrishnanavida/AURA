AURA Memory providers repository for storage_provider.

from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StorageProviderRepository:
    '''Repository for providers.storage_provider.'''

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._last_updated: Dict[str, float] = {}

    def save(self, key: str, item: Dict[str, Any]) -> None:
        '''Save item to the repository with metadata.'''
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._store[key] = {**item, "saved_at": time.time()}
            self._last_updated[key] = time.time()
            logger.debug("Saved item %s", key)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        '''Load item by key if it is still valid.'''
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            if time.time() - self._last_updated.get(key, 0.0) > self._ttl:
                self._store.pop(key, None)
                self._last_updated.pop(key, None)
                logger.debug("Expired item %s", key)
                return None
            return item.copy()

    def delete(self, key: str) -> bool:
        '''Delete item by key.'''
        with self._lock:
            self._last_updated.pop(key, None)
            return self._store.pop(key, None) is not None

    def list_keys(self) -> List[str]:
        '''List all valid keys.'''
        with self._lock:
            return list(self._store.keys())

    async def save_async(self, key: str, item: Dict[str, Any]) -> None:
        '''Async save wrapper.'''
        return self.save(key, item)


__all__ = ["StorageProviderRepository"]
