"""Episodic memory engine with replay and temporal ordering."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Store episodic events and replay them by recency and salience."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._episodes_processed = 0
        self._episodes: List[Dict[str, Any]] = []

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
            self._episodes_processed += 1
            episode = {
                "id": str(payload.get("id", f"episode-{self._episodes_processed}")),
                "content": payload.get("content", ""),
                "timestamp": float(payload.get("timestamp", time.time())),
                "importance": float(payload.get("importance", 0.5)),
            }
            self._episodes.append(episode)
            replay = self._replay(3)
        return {
            "status": "processed",
            "module": self.__class__.__name__,
            "payload": payload,
            "episodes_processed": self._episodes_processed,
            "replay": replay,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "started_at": self._started_at,
            "episodes_processed": self._episodes_processed,
            "episode_count": len(self._episodes),
        }

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _replay(self, limit: int) -> List[Dict[str, Any]]:
        sorted_episodes = sorted(self._episodes, key=lambda item: (item["timestamp"], item["importance"]), reverse=True)
        return sorted_episodes[:limit]


__all__ = ["Engine"]
