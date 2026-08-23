"""Search engine with BM25-style ranking and hybrid query support."""

from __future__ import annotations

import logging
import threading
import time
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SearchEngine:
    """Execute keyword-style searches and rank documents by relevance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._documents: List[Dict[str, Any]] = []

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
            documents = payload.get("documents", [])
            if not isinstance(documents, list):
                raise TypeError("documents must be a list")
            self._documents = documents
            results = self._search(query, documents)
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "results": results}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "document_count": len(self._documents)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tokens = query.split()
        if not tokens:
            return []
        doc_freq = Counter(token for doc in documents for token in self._tokenize(str(doc.get("content", ""))))
        results: List[Dict[str, Any]] = []
        for doc in documents:
            content = str(doc.get("content", ""))
            freq = Counter(self._tokenize(content))
            score = 0.0
            for token in tokens:
                count = freq.get(token, 0)
                if count:
                    score += (1.0 + count) / (1.0 + doc_freq[token])
            results.append({**doc, "score": round(score, 4)})
        return sorted(results, key=lambda item: item["score"], reverse=True)

    def _tokenize(self, text: str) -> List[str]:
        return [token for token in text.lower().replace("/", " ").split() if token]


__all__ = ["SearchEngine"]
