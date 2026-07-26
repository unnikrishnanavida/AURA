"""State model for providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProviderStatus(str, Enum):
    """Lifecycle status values for a provider."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass(slots=True)
class ProviderState:
    """Runtime state for a provider instance."""

    name: str
    status: ProviderStatus = ProviderStatus.IDLE
    last_error: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def set_status(self, status: ProviderStatus | str, error: str | None = None) -> None:
        """Transition to a new provider status."""
        self.status = ProviderStatus(status) if isinstance(status, str) else status
        self.last_error = error

    def mark_ready(self) -> None:
        """Mark the provider as ready."""
        self.set_status(ProviderStatus.READY)

    def mark_failed(self, error: str) -> None:
        """Mark the provider as failed."""
        self.set_status(ProviderStatus.FAILED, error)

    def to_dict(self) -> dict[str, object]:
        """Serialize the current state."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }
