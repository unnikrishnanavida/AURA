"""Working memory engine with activation and rehearsal logic."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Manage working memory items with activation, competition, and rehearsal."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._cycle_count = 0
        self._items: Dict[str, Dict[str, Any]] = {}
        self._capacity = int(self.config.get("capacity", 64))

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
            self._cycle_count += 1
            item_id = str(payload.get("id", f"item-{self._cycle_count}"))
            importance = float(payload.get("importance", 1.0))
            activation = self._score_activation(importance, self._cycle_count)
            self._items[item_id] = {
                "id": item_id,
                "content": payload.get("content", ""),
                "importance": importance,
                "activation": activation,
                "rehearsal_count": 0,
            }
            self._trim_to_capacity()
            ranked = self._rank_items()
        return {
            "status": "processed",
            "module": self.__class__.__name__,
            "payload": payload,
            "cycle_count": self._cycle_count,
            "items": ranked,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "started_at": self._started_at,
            "cycle_count": self._cycle_count,
            "item_count": len(self._items),
        }

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def rehearse(self, item_id: str, *, strength: float = 1.0) -> Dict[str, Any]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                raise KeyError(item_id)
            item["rehearsal_count"] += 1
            item["activation"] = self._score_activation(item["importance"], item["rehearsal_count"] + self._cycle_count, rehearsal=True, strength=strength)
            return {"id": item_id, "activation": item["activation"], "rehearsal_count": item["rehearsal_count"]}

    def _score_activation(self, importance: float, cycle: int, *, rehearsal: bool = False, strength: float = 1.0) -> float:
        base = importance * 0.7 + (cycle / 100.0) * 0.3
        if rehearsal:
            base += strength * 0.2
        return round(min(base, 1.0), 4)

    def _trim_to_capacity(self) -> None:
        if len(self._items) <= self._capacity:
            return
        ordered = sorted(self._items.items(), key=lambda entry: entry[1]["activation"], reverse=True)
        survivors = ordered[: self._capacity]
        self._items = {item_id: data for item_id, data in survivors}

    def _rank_items(self) -> List[Dict[str, Any]]:
        ranked = sorted(self._items.values(), key=lambda item: item["activation"], reverse=True)
        return [
            {
                "id": item["id"],
                "importance": item["importance"],
                "activation": item["activation"],
                "rehearsal_count": item["rehearsal_count"],
            }
            for item in ranked
        ]


__all__ = ["Engine"]
