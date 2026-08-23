"""Task memory engine with progress and urgency estimation."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Track tasks and estimate urgency from remaining work and deadlines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._tasks: List[Dict[str, Any]] = []

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
            task = {
                "id": str(payload.get("id", f"task-{len(self._tasks)+1}")),
                "title": payload.get("title", ""),
                "remaining": float(payload.get("remaining", 1.0)),
                "deadline": float(payload.get("deadline", time.time() + 60)),
            }
            self._tasks.append(task)
            ranked = self._rank_tasks()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "tasks": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "task_count": len(self._tasks)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _rank_tasks(self) -> List[Dict[str, Any]]:
        def urgency(task: Dict[str, Any]) -> float:
            return max(0.0, (1.0 - task["remaining"]) + (1.0 / max(1.0, task["deadline"] - time.time())))

        return sorted(self._tasks, key=lambda item: urgency(item), reverse=True)


__all__ = ["Engine"]
