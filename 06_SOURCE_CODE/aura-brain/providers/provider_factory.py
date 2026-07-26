"""Factory for creating provider instances."""

from __future__ import annotations

from .exceptions import ProviderConfigurationError
from .provider import Provider
from .provider_config import ProviderConfig
from .provider_registry import ProviderRegistry


class ProviderFactory:
    """Construct provider implementations from registry entries."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()

    def register(self, provider_cls: type[Provider], aliases: list[str] | None = None) -> None:
        """Register a provider implementation."""
        self.registry.register(provider_cls, aliases=aliases)

    def create(self, provider_name: str, config: ProviderConfig | None = None) -> Provider:
        """Create a provider instance by name."""
        provider_cls = self.registry.get(provider_name)
        if config is None:
            config = ProviderConfig(name=provider_name)
        config.validate()
        if not config.name:
            raise ProviderConfigurationError("Provider configuration must include a name.")
        return provider_cls(config)
