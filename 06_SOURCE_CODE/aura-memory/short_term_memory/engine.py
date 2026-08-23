"""Short-term memory engine with rehearsal and decay."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Maintain short-lived memory items with adaptive rehearsal and decay."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._items: Dict[str, Dict[str, Any]] = {}
        self._decay_rate = float(self.config.get("decay_rate", 0.1))

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
            item_id = str(payload.get("id", f"stm-{len(self._items)+1}"))
            item = {
                "id": item_id,
                "content": payload.get("content", ""),
                "strength": float(payload.get("strength", 1.0)),
                "rehearsal_count": 0,
                "last_updated": time.time(),
            }
            self._items[item_id] = item
            self._apply_decay()
            ranked = self._rank_items()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "items": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "item_count": len(self._items)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def rehearse(self, item_id: str) -> Dict[str, Any]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                raise KeyError(item_id)
            item["rehearsal_count"] += 1
            item["strength"] = min(1.0, item["strength"] + 0.15)
            item["last_updated"] = time.time()
            return {"id": item_id, "strength": item["strength"], "rehearsal_count": item["rehearsal_count"]}

    def _apply_decay(self) -> None:
        now = time.time()
        for item in self._items.values():
            age = max(0.0, now - item["last_updated"])
            item["strength"] = max(0.0, item["strength"] - self._decay_rate * age)

    def _rank_items(self) -> List[Dict[str, Any]]:
        return [
            {"id": item["id"], "strength": round(item["strength"], 4), "rehearsal_count": item["rehearsal_count"]}
            for item in sorted(self._items.values(), key=lambda entry: entry["strength"], reverse=True)
        ]


__all__ = ["Engine"]
