from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SystemStatus:
    status: str = "unknown"
    metrics: Dict[str, Any] = None

    def as_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "metrics": self.metrics or {}}
