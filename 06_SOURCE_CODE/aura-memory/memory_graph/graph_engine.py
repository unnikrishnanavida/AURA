"""Memory graph engine with traversal and centrality hints."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GraphEngine:
    """Track memory nodes and edges, then expose traversal and centrality summaries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []

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
            node_id = str(payload.get("node_id", f"node-{len(self._nodes)+1}"))
            self._nodes[node_id] = {"id": node_id, "weight": float(payload.get("weight", 1.0))}
            if payload.get("edge_to"):
                self._edges.append({"from": node_id, "to": str(payload["edge_to"]), "weight": float(payload.get("edge_weight", 1.0))})
            traversal = self._traverse(node_id)
            centrality = self._centrality(node_id)
        return {"status": "processed", "module": self.__class__.__name__, "payload": payload, "traversal": traversal, "centrality": centrality}

    def health(self) -> Dict[str, Any]:
        return {"active": self._active, "started_at": self._started_at, "node_count": len(self._nodes), "edge_count": len(self._edges)}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(payload)

    def _traverse(self, node_id: str) -> List[str]:
        return [edge["to"] for edge in self._edges if edge["from"] == node_id]

    def _centrality(self, node_id: str) -> float:
        degree = sum(1 for edge in self._edges if edge["from"] == node_id or edge["to"] == node_id)
        return round(degree / max(1, len(self._nodes)), 4)


__all__ = ["GraphEngine"]
