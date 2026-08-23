"""AURA SDK Providers exceptions."""


class ProviderError(Exception):
    """Base exception for aura_sdk.providers."""


class ProviderNotFoundError(ProviderError):
    """Raised when a providers resource is missing."""


class ProviderValidationError(ProviderError):
    """Raised when a providers resource fails validation."""


__all__ = [
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderValidationError",
]
