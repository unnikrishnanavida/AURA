"""Health model for providers."""

from __future__ import annotations

from dataclasses import dataclass

from .provider_state import ProviderStatus


@dataclass(slots=True)
class ProviderHealth:
    """Represents the health status of a provider."""

    healthy: bool
    message: str = ""
    latency_ms: int | None = None
    status: ProviderStatus | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the health report."""
        return {
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "status": self.status.value if self.status else None,
        }
