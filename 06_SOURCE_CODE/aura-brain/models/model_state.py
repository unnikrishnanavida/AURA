"""State model for models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ModelStatus(str, Enum):
    """Lifecycle status values for a model."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass(slots=True)
class ModelState:
    """Runtime state for a model instance."""

    name: str
    status: ModelStatus = ModelStatus.IDLE
    last_error: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def set_status(self, status: ModelStatus | str, error: str | None = None) -> None:
        """Transition to a new model status."""
        self.status = ModelStatus(status) if isinstance(status, str) else status
        self.last_error = error

    def mark_ready(self) -> None:
        """Mark the model as ready."""
        self.set_status(ModelStatus.READY)

    def mark_failed(self, error: str) -> None:
        """Mark the model as failed."""
        self.set_status(ModelStatus.FAILED, error)

    def to_dict(self) -> dict[str, object]:
        """Serialize the current state."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }
