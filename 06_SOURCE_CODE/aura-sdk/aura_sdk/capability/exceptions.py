"""AURA SDK Capability exceptions."""


class CapabilityError(Exception):
    """Base exception for aura_sdk.capability."""


class CapabilityNotFoundError(CapabilityError):
    """Raised when a capability resource is missing."""


class CapabilityValidationError(CapabilityError):
    """Raised when a capability resource fails validation."""


__all__ = [
    "CapabilityError",
    "CapabilityNotFoundError",
    "CapabilityValidationError",
]
