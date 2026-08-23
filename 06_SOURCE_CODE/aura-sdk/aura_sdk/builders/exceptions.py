"""AURA SDK Builders exceptions."""


class BuilderError(Exception):
    """Base exception for aura_sdk.builders."""


class BuilderNotFoundError(BuilderError):
    """Raised when a builders resource is missing."""


class BuilderValidationError(BuilderError):
    """Raised when a builders resource fails validation."""


__all__ = [
    "BuilderError",
    "BuilderNotFoundError",
    "BuilderValidationError",
]
