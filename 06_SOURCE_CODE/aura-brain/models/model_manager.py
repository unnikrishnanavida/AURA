"""Runtime manager for models with safer lifecycle handling."""

from __future__ import annotations

from .exceptions import ModelNotFoundError
from .model import Model
from .model_config import ModelConfig
from .model_factory import ModelFactory
from .model_registry import ModelRegistry
from .model_state import ModelStatus


class ModelManager:
    """Coordinate model lifecycle, creation, and health."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()
        self.factory = ModelFactory(self.registry)
        self._models: dict[str, Model] = {}

    def register(self, model: type[Model], aliases: list[str] | None = None) -> None:
        """Register a model implementation."""
        self.factory.register(model, aliases=aliases)

    def create(self, model_name: str, config: ModelConfig | None = None, *, allow_recreate: bool = False) -> Model:
        """Create and initialize a model instance."""
        normalized_name = self._normalize_name(model_name)
        if normalized_name in self._models and not allow_recreate:
            return self._models[normalized_name]

        instance = self.factory.create(model_name, config)
        try:
            instance.initialize()
            instance.set_state(ModelStatus.READY)
        except Exception as exc:  # pragma: no cover - defensive path
            instance.set_state(ModelStatus.FAILED, str(exc))
            raise

        self._models[normalized_name] = instance
        return instance

    def get(self, model_name: str) -> Model:
        """Return a previously created model."""
        normalized_name = self._normalize_name(model_name)
        if normalized_name not in self._models:
            raise ModelNotFoundError(f"Model '{model_name}' is not managed.")
        return self._models[normalized_name]

    def get_or_create(self, model_name: str, config: ModelConfig | None = None) -> Model:
        """Return an existing model or create a new one."""
        try:
            return self.get(model_name)
        except ModelNotFoundError:
            return self.create(model_name, config)

    def remove(self, model_name: str) -> None:
        """Remove a managed model from the manager."""
        normalized_name = self._normalize_name(model_name)
        model = self._models.pop(normalized_name, None)
        if model is not None:
            model.shutdown()

    def list(self) -> list[str]:
        """Return the managed model names."""
        return sorted(self._models)

    def health_check_all(self) -> dict[str, object]:
        """Run health checks for all managed models."""
        return {name: self._models[name].health_check() for name in self.list()}

    def shutdown_all(self) -> None:
        """Shutdown all managed models."""
        for model in list(self._models.values()):
            model.shutdown()
        self._models.clear()

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower()
