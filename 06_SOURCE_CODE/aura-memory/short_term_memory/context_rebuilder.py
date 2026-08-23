AURA Memory short_term_memory service for context_rebuilder.

from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ContextRebuilder:
    '''Service component for short_term_memory.context_rebuilder.'''

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        '''Start the service.'''
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info("Started %s", self.__class__.__name__)

    def stop(self) -> None:
        '''Stop the service.'''
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info("Stopped %s", self.__class__.__name__)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Execute processing logic.'''
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"status": "ok", "module": self.__class__.__name__, "payload": payload}

    async def execute_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Async execution wrapper.'''
        return self.execute(payload)


__all__ = ["ContextRebuilder"]
