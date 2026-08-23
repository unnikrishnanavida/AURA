"""Long-term memory engine with consolidation and retention logic."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Store durable memory traces and consolidate them over time."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._items: Dict[str, Dict[str, Any]] = {}
        self._retention_threshold = float(self.config.get("retention_threshold", 0.25))

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
            item_id = str(payload.get("id", f"ltm-{len(self._items)+1}"))
            item = {
                "id": item_id,
                "content": payload.get("content", ""),
                "importance": float(payload.get("importance", 0.5)),
                "retention": float(payload.get("retention", 0.5)),
                "consolidated": False,
            }
            self._items[item_id] = item
            self._consolidate()
            ranked = self._rank_items()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "items": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "item_count": len(self._items)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def consolidate(self, item_id: str) -> Dict[str, Any]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                raise KeyError(item_id)
            item["consolidated"] = True
            item["retention"] = min(1.0, item["retention"] + 0.1 * item["importance"])
            return {"id": item_id, "consolidated": item["consolidated"], "retention": item["retention"]}

    def _consolidate(self) -> None:
        for item in self._items.values():
            if item["importance"] >= self._retention_threshold:
                item["consolidated"] = True
                item["retention"] = min(1.0, item["retention"] + 0.05)

    def _rank_items(self) -> List[Dict[str, Any]]:
        return [
            {"id": item["id"], "importance": item["importance"], "retention": round(item["retention"], 4), "consolidated": item["consolidated"]}
            for item in sorted(self._items.values(), key=lambda entry: entry["retention"], reverse=True)
        ]


__all__ = ["Engine"]
