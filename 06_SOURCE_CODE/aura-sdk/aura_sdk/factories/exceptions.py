"""AURA SDK Factories exceptions."""


class FactorieError(Exception):
    """Base exception for aura_sdk.factories."""


class FactorieNotFoundError(FactorieError):
    """Raised when a factories resource is missing."""


class FactorieValidationError(FactorieError):
    """Raised when a factories resource fails validation."""


__all__ = [
    "FactorieError",
    "FactorieNotFoundError",
    "FactorieValidationError",
]
