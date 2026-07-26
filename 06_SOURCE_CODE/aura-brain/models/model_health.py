"""Health model for models."""

from __future__ import annotations

from dataclasses import dataclass

from .model_state import ModelStatus


@dataclass(slots=True)
class ModelHealth:
    """Represents the health status of a model."""

    healthy: bool
    message: str = ""
    latency_ms: int | None = None
    status: ModelStatus | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the health report."""
        return {
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "status": self.status.value if self.status else None,
        }
