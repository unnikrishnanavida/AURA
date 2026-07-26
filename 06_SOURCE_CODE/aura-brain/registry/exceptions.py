"""Registry-specific exceptions."""

from __future__ import annotations


class RegistryError(Exception):
    """Base exception for registry failures."""


class RegistryNotFoundError(RegistryError):
    """Raised when a registry entry cannot be found."""


class RegistryConflictError(RegistryError):
    """Raised for duplicate registration attempts."""


class RegistryValidationError(RegistryError):
    """Raised when registry data is invalid."""
