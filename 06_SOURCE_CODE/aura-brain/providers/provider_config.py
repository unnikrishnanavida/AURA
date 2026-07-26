"""Configuration model for providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderConfig:
    """Configuration container for a provider instance."""

    name: str
    endpoint: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout: int = 30
    retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValueError("ProviderConfig.name must be provided")
        if self.timeout <= 0:
            raise ValueError("ProviderConfig.timeout must be greater than zero")
        if self.retries < 0:
            raise ValueError("ProviderConfig.retries must be non-negative")

    def validate(self) -> None:
        """Validate the configuration without raising on optional fields."""
        if not self.name:
            raise ValueError("ProviderConfig.name must be provided")
        if self.timeout <= 0:
            raise ValueError("ProviderConfig.timeout must be greater than zero")
        if self.retries < 0:
            raise ValueError("ProviderConfig.retries must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration."""
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "api_key": self.api_key,
            "model": self.model,
            "timeout": self.timeout,
            "retries": self.retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        """Create a config from a dictionary."""
        return cls(**data)
