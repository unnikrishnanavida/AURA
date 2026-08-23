"""AURA SDK Explainability exceptions."""


class ExplainabilityError(Exception):
    """Base exception for aura_sdk.explainability."""


class ExplainabilityNotFoundError(ExplainabilityError):
    """Raised when a explainability resource is missing."""


class ExplainabilityValidationError(ExplainabilityError):
    """Raised when a explainability resource fails validation."""


__all__ = [
    "ExplainabilityError",
    "ExplainabilityNotFoundError",
    "ExplainabilityValidationError",
]
