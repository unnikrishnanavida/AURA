"""AURA SDK Discovery exceptions."""


class DiscoveryError(Exception):
    """Base exception for aura_sdk.discovery."""


class DiscoveryNotFoundError(DiscoveryError):
    """Raised when a discovery resource is missing."""


class DiscoveryValidationError(DiscoveryError):
    """Raised when a discovery resource fails validation."""


__all__ = [
    "DiscoveryError",
    "DiscoveryNotFoundError",
    "DiscoveryValidationError",
]
