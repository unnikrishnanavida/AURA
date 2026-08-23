"""Semantic memory engine with concept linkage and relevance scoring."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Store semantic facts and score their relevance to incoming queries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._processed_count = 0
        self._facts: Dict[str, Dict[str, Any]] = {}

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
            fact_id = str(payload.get("id", f"fact-{self._processed_count}"))
            fact = {
                "id": fact_id,
                "content": payload.get("content", ""),
                "concepts": payload.get("concepts", []),
                "strength": float(payload.get("strength", 0.5)),
            }
            self._facts[fact_id] = fact
            related = self._score_relevance(payload.get("query", ""))
        return {
            "status": "processed",
            "module": self.__class__.__name__,
            "payload": payload,
            "processed_count": self._processed_count,
            "related_facts": related,
        }

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "processed_count": self._processed_count, "fact_count": len(self._facts)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _score_relevance(self, query: str) -> List[Dict[str, Any]]:
        if not query:
            return []
        query_terms = set(str(query).lower().split())
        scored: List[Dict[str, Any]] = []
        for fact in self._facts.values():
            concepts = {str(token).lower() for token in fact.get("concepts", [])}
            overlap = len(query_terms & concepts)
            score = round(min(1.0, overlap * 0.35 + fact["strength"] * 0.65), 4)
            scored.append({"id": fact["id"], "score": score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)


__all__ = ["Engine"]
