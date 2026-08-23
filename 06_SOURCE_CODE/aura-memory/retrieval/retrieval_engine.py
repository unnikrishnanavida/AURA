"""Retrieval engine with hybrid ranking and context scoring."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """Retrieve candidate memories using keyword, semantic, and contextual signals."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._items: List[Dict[str, Any]] = []

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
            query = str(payload.get("query", "")).lower()
            candidates = payload.get("candidates", [])
            if not isinstance(candidates, list):
                raise TypeError("candidates must be a list")
            ranked = self._rank_candidates(query, candidates)
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "results": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "candidate_count": len(self._items)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _rank_candidates(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for candidate in candidates:
            text = str(candidate.get("content", "")).lower()
            keyword_score = 1.0 if query and query in text else 0.0
            semantic_score = 0.6 if query and query.split()[0] in text else 0.0
            context_score = float(candidate.get("context_score", 0.0))
            final_score = round(keyword_score * 0.6 + semantic_score * 0.2 + context_score * 0.2, 4)
            scored.append({**candidate, "score": final_score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)


__all__ = ["RetrievalEngine"]
