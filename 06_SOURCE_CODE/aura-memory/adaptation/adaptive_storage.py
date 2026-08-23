"""AURA Memory Adaptation Adaptive Storage repository."""

from __future__ import annotations
import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class AdaptiveStorageRepository:
    """Repository for adaptation.adaptive_storage."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, key: str, item: Dict[str, Any]) -> None:
        """Save item to repository."""
        if not key:
            raise ValueError('key must be non-empty')
        with self._lock:
            self._store[key] = item.copy()
            logger.debug('Saved item %s', key)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load item by key."""
        with self._lock:
            return self._store.get(key)

    def delete(self, key: str) -> bool:
        """Delete item by key."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def list_keys(self) -> List[str]:
        """List stored keys."""
        with self._lock:
            return list(self._store.keys())

    async def save_async(self, key: str, item: Dict[str, Any]) -> None:
        """Async save wrapper."""
        return self.save(key, item)

__all__ = ['AdaptiveStorageRepository']
