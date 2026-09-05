"""Flight recorder event model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionEvent:
    """One recorded execution event."""

    timestamp: float
    execution_id: str
    event: str
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "execution_id": self.execution_id,
            "event": self.event,
            "data": dict(self.data),
        }


__all__ = ["ExecutionEvent"]