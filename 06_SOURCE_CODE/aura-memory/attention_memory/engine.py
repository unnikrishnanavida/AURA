"""Attention memory engine with salience-based allocation."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Allocate attention to salient items and rank them by importance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._items: List[Dict[str, Any]] = []

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info("Started %s", self.__class__.__name__)

    def shutdown(self) -> None:
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info("Stopped %s", self.__class__.__name__)

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        with self._lock:
            items = payload.get("items", [])
            if not isinstance(items, list):
                raise TypeError("items must be a list")
            self._items = [{**item, "attention": float(item.get("importance", 0.0))} for item in items]
            ranked = self._rank_items()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "items": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "item_count": len(self._items)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _rank_items(self) -> List[Dict[str, Any]]:
        return sorted(self._items, key=lambda item: item["attention"], reverse=True)


__all__ = ["Engine"]
