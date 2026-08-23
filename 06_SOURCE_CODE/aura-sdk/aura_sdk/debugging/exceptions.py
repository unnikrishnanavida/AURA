"""AURA SDK Debugging exceptions."""


class DebuggingError(Exception):
    """Base exception for aura_sdk.debugging."""


class DebuggingNotFoundError(DebuggingError):
    """Raised when a debugging resource is missing."""


class DebuggingValidationError(DebuggingError):
    """Raised when a debugging resource fails validation."""


__all__ = [
    "DebuggingError",
    "DebuggingNotFoundError",
    "DebuggingValidationError",
]
