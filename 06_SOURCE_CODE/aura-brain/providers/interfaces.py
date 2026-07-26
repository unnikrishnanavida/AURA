"""Protocol interfaces for provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .provider_health import ProviderHealth


class ProviderLifecycle(ABC):
    """Lifecycle contract for providers."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the provider."""

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Report provider health."""


class ProviderProtocol(ABC):
    """Execution contract for providers."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a provider operation."""
