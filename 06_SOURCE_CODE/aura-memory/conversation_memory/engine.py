"""Conversation memory engine with topic summarization."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Track conversational turns and produce lightweight topic summaries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._turns: List[Dict[str, Any]] = []

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
            turn = {
                "id": str(payload.get("id", f"turn-{len(self._turns)+1}")),
                "text": payload.get("text", ""),
                "topic": payload.get("topic", "general"),
            }
            self._turns.append(turn)
            summary = self._summarize_topics()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "summary": summary}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "turn_count": len(self._turns)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _summarize_topics(self) -> Dict[str, int]:
        topics: Dict[str, int] = {}
        for turn in self._turns:
            topic = str(turn.get("topic", "general"))
            topics[topic] = topics.get(topic, 0) + 1
        return topics


__all__ = ["Engine"]
