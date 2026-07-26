"""Core model abstraction with production-oriented lifecycle support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .model_capability import ModelCapability
from .model_config import ModelConfig
from .model_health import ModelHealth
from .model_metrics import ModelMetrics
from .model_state import ModelState, ModelStatus


class Model(ABC):
    """Base interface for all model implementations."""

    name: str = "model"

    def __init__(self, config: ModelConfig | None = None) -> None:
        self.config = config or ModelConfig(name=self.name)
        self.config.validate()
        self.state = ModelState(name=self.config.name or self.name)
        self.metrics = ModelMetrics()
        self._capabilities: list[ModelCapability] = []

    @property
    def capabilities(self) -> list[ModelCapability]:
        """Return the model capabilities."""
        return list(self._capabilities)

    def register_capability(self, capability: ModelCapability) -> None:
        """Register a capability exposed by the model."""
        self._capabilities.append(capability)

    def set_state(self, status: ModelStatus | str, error: str | None = None) -> None:
        """Update model runtime state."""
        self.state.set_status(status, error)

    def is_ready(self) -> bool:
        """Return whether the model is ready for inference."""
        return self.state.status == ModelStatus.READY

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the model."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the model."""

    @abstractmethod
    def health_check(self) -> ModelHealth:
        """Return current health."""

    def get_metrics(self) -> ModelMetrics:
        """Return runtime metrics for the model."""
        return self.metrics

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the model operation."""
        raise NotImplementedError(f"{self.__class__.__name__} does not implement execution")

    def close(self) -> None:
        """Compatibility wrapper around shutdown."""
        self.shutdown()
