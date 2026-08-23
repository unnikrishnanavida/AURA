"""Associative memory engine with spreading activation and link strength."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Maintain associations between memory items and spread activation to related nodes."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._processed_count = 0
        self._links: Dict[str, Dict[str, Any]] = {}

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
            source = str(payload.get("source", f"node-{self._processed_count}"))
            target = str(payload.get("target", f"node-{self._processed_count+1}"))
            strength = float(payload.get("strength", 0.5))
            self._links[source + "->" + target] = {"source": source, "target": target, "strength": strength}
            activations = self._spread_activation(source)
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "activations": activations}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "processed_count": self._processed_count, "link_count": len(self._links)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _spread_activation(self, source: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for link in self._links.values():
            if link["source"] == source:
                results.append({"target": link["target"], "strength": round(link["strength"], 4)})
        return results


__all__ = ["Engine"]
