"""Gemini provider adapter."""

from __future__ import annotations

from ..provider import Provider
from ..provider_config import ProviderConfig
from ..provider_health import ProviderHealth
from ..provider_state import ProviderStatus


class GeminiProvider(Provider):
    """Adapter for Gemini-backed model access."""

    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)

    name = "gemini"

    def initialize(self) -> None:
        self.set_state(ProviderStatus.INITIALIZING)
        self.register_capability(self._build_default_capability())
        self.set_state(ProviderStatus.READY)

    def shutdown(self) -> None:
        self.set_state(ProviderStatus.SHUTDOWN)

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=self.is_ready(),
            message="Gemini provider ready",
            status=self.state.status,
        )

    def _build_default_capability(self) -> object:
        from ..provider_capability import ProviderCapability

        return ProviderCapability(name="multimodal", description="Gemini multimodal access")
