AURA Memory cluster manager for cluster_manager.

from __future__ import annotations
import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClusterManager:
    '''Manager for cluster.cluster_manager.'''

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: Dict[str, Any] = {}

    def register(self, key: str, item: Any) -> None:
        '''Register an item.'''
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._items[key] = item
            logger.debug("Registered %s", key)

    def get(self, key: str) -> Optional[Any]:
        '''Get an item by key.'''
        with self._lock:
            return self._items.get(key)

    def list_keys(self) -> List[str]:
        '''List all registered keys.'''
        with self._lock:
            return list(self._items.keys())

    def remove(self, key: str) -> bool:
        '''Remove an item.'''
        with self._lock:
            return self._items.pop(key, None) is not None


__all__ = ["ClusterManager"]
