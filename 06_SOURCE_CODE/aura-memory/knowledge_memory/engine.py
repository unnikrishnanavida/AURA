"""Knowledge memory engine with concept consolidation."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Store knowledge items and consolidate repeated concepts."""

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
            item = {
                "id": str(payload.get("id", f"knowledge-{len(self._items)+1}")),
                "content": payload.get("content", ""),
                "concepts": payload.get("concepts", []),
                "strength": float(payload.get("strength", 0.5)),
            }
            self._items.append(item)
            consolidated = self._consolidate()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "consolidated": consolidated}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "item_count": len(self._items)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _consolidate(self) -> List[Dict[str, Any]]:
        grouped: Dict[str, int] = {}
        for item in self._items:
            for concept in item.get("concepts", []):
                grouped[str(concept)] = grouped.get(str(concept), 0) + 1
        return [{"concept": concept, "count": count} for concept, count in sorted(grouped.items(), key=lambda pair: pair[1], reverse=True)]


__all__ = ["Engine"]
