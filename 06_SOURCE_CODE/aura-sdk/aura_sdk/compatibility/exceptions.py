"""AURA SDK Compatibility exceptions."""


class CompatibilityError(Exception):
    """Base exception for aura_sdk.compatibility."""


class CompatibilityNotFoundError(CompatibilityError):
    """Raised when a compatibility resource is missing."""


class CompatibilityValidationError(CompatibilityError):
    """Raised when a compatibility resource fails validation."""


__all__ = [
    "CompatibilityError",
    "CompatibilityNotFoundError",
    "CompatibilityValidationError",
]
