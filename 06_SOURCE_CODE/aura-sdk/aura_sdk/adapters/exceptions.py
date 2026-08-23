"""AURA SDK Adapters exceptions."""


class AdapterError(Exception):
    """Base exception for aura_sdk.adapters."""


class AdapterNotFoundError(AdapterError):
    """Raised when a adapters resource is missing."""


class AdapterValidationError(AdapterError):
    """Raised when a adapters resource fails validation."""


__all__ = [
    "AdapterError",
    "AdapterNotFoundError",
    "AdapterValidationError",
]
