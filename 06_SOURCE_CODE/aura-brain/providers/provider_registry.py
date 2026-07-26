"""Registry for provider implementations with alias support."""

from __future__ import annotations

from typing import Type

from .exceptions import ProviderNotFoundError
from .provider import Provider


class ProviderRegistry:
    """Registry that maps provider names to implementation classes."""

    def __init__(self) -> None:
        self._providers: dict[str, Type[Provider]] = {}
        self._aliases: dict[str, str] = {}

    def register(self, provider_cls: Type[Provider], aliases: list[str] | None = None) -> None:
        """Register a provider class and optional aliases."""
        canonical_name = self._normalize_name(getattr(provider_cls, "name", provider_cls.__name__))
        if not canonical_name:
            raise ValueError("Provider class must define a non-empty name.")

        if not issubclass(provider_cls, Provider):
            raise TypeError("Registered provider class must inherit from Provider")

        self._providers[canonical_name] = provider_cls
        for alias in aliases or []:
            self._aliases[self._normalize_name(alias)] = canonical_name

    def get(self, name: str) -> Type[Provider]:
        """Return a provider class by name."""
        normalized_name = self._normalize_name(name)
        if normalized_name in self._providers:
            return self._providers[normalized_name]
        if normalized_name in self._aliases:
            return self._providers[self._aliases[normalized_name]]
        raise ProviderNotFoundError(f"Provider '{name}' is not registered.")

    def list(self) -> list[str]:
        """Return all registered provider names."""
        return sorted(self._providers)

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower().replace("provider", "").strip()
