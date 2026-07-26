"""Anthropic provider adapter."""

from __future__ import annotations

from ..provider import Provider
from ..provider_config import ProviderConfig
from ..provider_health import ProviderHealth
from ..provider_state import ProviderStatus


class AnthropicProvider(Provider):
    """Adapter for Anthropic-backed model access."""

    name = "anthropic"

    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.set_state(ProviderStatus.INITIALIZING)
        self.register_capability(self._build_default_capability())
        self.set_state(ProviderStatus.READY)

    def shutdown(self) -> None:
        self.set_state(ProviderStatus.SHUTDOWN)

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=self.is_ready(),
            message="Anthropic provider ready",
            status=self.state.status,
        )

    def _build_default_capability(self) -> object:
        from ..provider_capability import ProviderCapability

        return ProviderCapability(name="reasoning", description="Anthropic reasoning access")
