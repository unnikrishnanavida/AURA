"""Procedural memory engine with skill reinforcement and execution scoring."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Engine:
    """Track procedures and reinforce those that repeatedly succeed."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._procedures: Dict[str, Dict[str, Any]] = {}

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
            procedure_id = str(payload.get("id", f"procedure-{len(self._procedures)+1}"))
            procedure = {
                "id": procedure_id,
                "name": payload.get("name", procedure_id),
                "successes": 0,
                "failures": 0,
            }
            self._procedures[procedure_id] = procedure
            ranked = self._rank_procedures()
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "procedures": ranked}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "procedure_count": len(self._procedures)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def reinforce(self, procedure_id: str, *, succeeded: bool) -> Dict[str, Any]:
        with self._lock:
            procedure = self._procedures.get(procedure_id)
            if not procedure:
                raise KeyError(procedure_id)
            if succeeded:
                procedure["successes"] += 1
            else:
                procedure["failures"] += 1
            return {"id": procedure_id, "successes": procedure["successes"], "failures": procedure["failures"]}

    def _rank_procedures(self) -> List[Dict[str, Any]]:
        return [
            {"id": procedure["id"], "name": procedure["name"], "score": round(procedure["successes"] / max(1, procedure["successes"] + procedure["failures"]), 4)}
            for procedure in sorted(self._procedures.values(), key=lambda item: item["successes"], reverse=True)
        ]


__all__ = ["Engine"]
