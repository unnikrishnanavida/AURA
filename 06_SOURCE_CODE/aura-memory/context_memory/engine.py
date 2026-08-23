"""Context memory engine with relevance and recency scoring."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Track contextual items and prioritize those that are both recent and relevant."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._contexts: List[Dict[str, Any]] = []

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
            context = {
                "id": str(payload.get("id", f"context-{len(self._contexts)+1}")),
                "content": payload.get("content", ""),
                "relevance": float(payload.get("relevance", 0.5)),
                "timestamp": float(payload.get("timestamp", time.time())),
            }
            self._contexts.append(context)
            ranked = self._rank_contexts()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "contexts": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "context_count": len(self._contexts)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _rank_contexts(self) -> List[Dict[str, Any]]:
        return sorted(self._contexts, key=lambda item: (item["timestamp"], item["relevance"]), reverse=True)


__all__ = ["Engine"]
