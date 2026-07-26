"""Provider-specific exceptions."""

from __future__ import annotations


class ProviderError(Exception):
    """Base exception for provider failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""


class ProviderInitializationError(ProviderError):
    """Raised when provider initialization fails."""


class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not registered or available."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot be reached."""
