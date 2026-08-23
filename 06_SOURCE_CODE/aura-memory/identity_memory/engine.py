"""Identity memory engine with salience and stability scoring."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Maintain identity-related memories and score their stability over time."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._entries: List[Dict[str, Any]] = []

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
            entry = {
                "id": str(payload.get("id", f"identity-{len(self._entries)+1}")),
                "content": payload.get("content", ""),
                "salience": float(payload.get("salience", 0.5)),
                "stability": float(payload.get("stability", 0.5)),
            }
            self._entries.append(entry)
            ranked = self._rank_entries()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "entries": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "entry_count": len(self._entries)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _rank_entries(self) -> List[Dict[str, Any]]:
        return sorted(self._entries, key=lambda item: item["salience"] + item["stability"], reverse=True)


__all__ = ["Engine"]
