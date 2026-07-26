"""Factory for creating model instances."""

from __future__ import annotations

from .exceptions import ModelConfigurationError
from .model import Model
from .model_config import ModelConfig
from .model_registry import ModelRegistry


class ModelFactory:
    """Construct model implementations from registry entries."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()

    def register(self, model_cls: type[Model], aliases: list[str] | None = None) -> None:
        """Register a model implementation."""
        self.registry.register(model_cls, aliases=aliases)

    def create(self, model_name: str, config: ModelConfig | None = None) -> Model:
        """Create a model instance by name."""
        model_cls = self.registry.get(model_name)
        if config is None:
            config = ModelConfig(name=model_name)
        config.validate()
        if not config.name:
            raise ModelConfigurationError("Model configuration must include a name.")
        return model_cls(config)
