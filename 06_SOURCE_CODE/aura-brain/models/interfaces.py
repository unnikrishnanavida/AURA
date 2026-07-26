"""Protocol interfaces for model implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .model_health import ModelHealth


class ModelLifecycle(ABC):
    """Lifecycle contract for models."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the model."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the model."""

    @abstractmethod
    def health_check(self) -> ModelHealth:
        """Report model health."""


class ModelProtocol(ABC):
    """Execution contract for models."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a model operation."""
