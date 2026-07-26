"""Gateway request models for the gateway subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GatewayRequest:
    """Represents a request entering the gateway."""

    route: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"route": self.route, "payload": self.payload, "metadata": self.metadata}
