"""AURA SDK Registry exceptions."""


class RegistryError(Exception):
    """Base exception for aura_sdk.registry."""


class RegistryNotFoundError(RegistryError):
    """Raised when a registry resource is missing."""


class RegistryValidationError(RegistryError):
    """Raised when a registry resource fails validation."""


__all__ = [
    "RegistryError",
    "RegistryNotFoundError",
    "RegistryValidationError",
]
