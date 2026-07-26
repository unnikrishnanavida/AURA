"""Runtime manager for providers with safer lifecycle handling."""

from __future__ import annotations

from .exceptions import ProviderNotFoundError
from .provider import Provider
from .provider_config import ProviderConfig
from .provider_factory import ProviderFactory
from .provider_registry import ProviderRegistry
from .provider_state import ProviderStatus


class ProviderManager:
    """Coordinate provider lifecycle, creation, and health."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.factory = ProviderFactory(self.registry)
        self._providers: dict[str, Provider] = {}

    def register(self, provider: type[Provider], aliases: list[str] | None = None) -> None:
        """Register a provider implementation."""
        self.factory.register(provider, aliases=aliases)

    def create(
        self,
        provider_name: str,
        config: ProviderConfig | None = None,
        *,
        allow_recreate: bool = False,
    ) -> Provider:
        """Create and initialize a provider instance."""
        normalized_name = self._normalize_name(provider_name)
        if normalized_name in self._providers and not allow_recreate:
            return self._providers[normalized_name]

        instance = self.factory.create(provider_name, config)
        try:
            instance.initialize()
            instance.set_state(ProviderStatus.READY)
        except Exception as exc:  # pragma: no cover - defensive path
            instance.set_state(ProviderStatus.FAILED, str(exc))
            raise

        self._providers[normalized_name] = instance
        return instance

    def get(self, provider_name: str) -> Provider:
        """Return a previously created provider."""
        normalized_name = self._normalize_name(provider_name)
        if normalized_name not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_name}' is not managed.")
        return self._providers[normalized_name]

    def get_or_create(self, provider_name: str, config: ProviderConfig | None = None) -> Provider:
        """Return an existing provider or create a new one."""
        try:
            return self.get(provider_name)
        except ProviderNotFoundError:
            return self.create(provider_name, config)

    def remove(self, provider_name: str) -> None:
        """Remove a managed provider from the manager."""
        normalized_name = self._normalize_name(provider_name)
        provider = self._providers.pop(normalized_name, None)
        if provider is not None:
            provider.shutdown()

    def list(self) -> list[str]:
        """Return the managed provider names."""
        return sorted(self._providers)

    def health_check_all(self) -> dict[str, object]:
        """Run health checks for all managed providers."""
        return {name: self._providers[name].health_check() for name in self.list()}

    def shutdown_all(self) -> None:
        """Shutdown all managed providers."""
        for provider in list(self._providers.values()):
            provider.shutdown()
        self._providers.clear()

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower()
