"""Gateway response models for the gateway subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GatewayResponse:
    """Represents a response produced by gateway handlers."""

    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        return self.status.lower() == "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
