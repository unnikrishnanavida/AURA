"""AURA SDK Observability exceptions."""


class ObservabilityError(Exception):
    """Base exception for aura_sdk.observability."""


class ObservabilityNotFoundError(ObservabilityError):
    """Raised when a observability resource is missing."""


class ObservabilityValidationError(ObservabilityError):
    """Raised when a observability resource fails validation."""


__all__ = [
    "ObservabilityError",
    "ObservabilityNotFoundError",
    "ObservabilityValidationError",
]
