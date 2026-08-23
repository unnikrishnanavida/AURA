"""Memory engine for the AURA memory subsystem."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Simple stateful engine for memory operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._processed_count = 0

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
            self._processed_count += 1
        return {
            "status": "processed",
            "module": self.__class__.__name__,
            "payload": payload,
            "processed_count": self._processed_count,
        }

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "processed_count": self._processed_count}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)


__all__ = ["Engine"]
