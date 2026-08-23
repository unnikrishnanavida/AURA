"""Reasoning engine with rule-based inference and confidence estimation."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Produce simple causal or deductive traces from observations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._observations: List[Dict[str, Any]] = []

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
            observation = {
                "id": str(payload.get("id", f"obs-{len(self._observations)+1}")),
                "content": payload.get("content", ""),
                "confidence": float(payload.get("confidence", 0.5)),
            }
            self._observations.append(observation)
            inference = self._infer(observation)
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "inference": inference}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "observation_count": len(self._observations)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _infer(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        confidence = min(1.0, observation["confidence"] + 0.1)
        return {"conclusion": f"Observed {observation['content']}", "confidence": round(confidence, 4)}


__all__ = ["ReasoningEngine"]
