"""Registry for model implementations with alias support."""

from __future__ import annotations

from typing import Type

from .exceptions import ModelNotFoundError
from .model import Model


class ModelRegistry:
    """Registry that maps model names to implementation classes."""

    def __init__(self) -> None:
        self._models: dict[str, Type[Model]] = {}
        self._aliases: dict[str, str] = {}

    def register(self, model_cls: Type[Model], aliases: list[str] | None = None) -> None:
        """Register a model class and optional aliases."""
        canonical_name = self._normalize_name(getattr(model_cls, "name", model_cls.__name__))
        if not canonical_name:
            raise ValueError("Model class must define a non-empty name.")

        if not issubclass(model_cls, Model):
            raise TypeError("Registered model class must inherit from Model")

        self._models[canonical_name] = model_cls
        for alias in aliases or []:
            self._aliases[self._normalize_name(alias)] = canonical_name

    def get(self, name: str) -> Type[Model]:
        """Return a model class by name."""
        normalized_name = self._normalize_name(name)
        if normalized_name in self._models:
            return self._models[normalized_name]
        if normalized_name in self._aliases:
            return self._models[self._aliases[normalized_name]]
        raise ModelNotFoundError(f"Model '{name}' is not registered.")

    def list(self) -> list[str]:
        """Return all registered model names."""
        return sorted(self._models)

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower()
