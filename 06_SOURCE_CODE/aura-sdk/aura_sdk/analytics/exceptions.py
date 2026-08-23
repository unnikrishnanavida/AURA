"""AURA SDK Analytics exceptions."""


class AnalyticError(Exception):
    """Base exception for aura_sdk.analytics."""


class AnalyticNotFoundError(AnalyticError):
    """Raised when a analytics resource is missing."""


class AnalyticValidationError(AnalyticError):
    """Raised when a analytics resource fails validation."""


__all__ = [
    "AnalyticError",
    "AnalyticNotFoundError",
    "AnalyticValidationError",
]
