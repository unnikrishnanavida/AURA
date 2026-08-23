"""AURA SDK Optimization exceptions."""


class OptimizationError(Exception):
    """Base exception for aura_sdk.optimization."""


class OptimizationNotFoundError(OptimizationError):
    """Raised when a optimization resource is missing."""


class OptimizationValidationError(OptimizationError):
    """Raised when a optimization resource fails validation."""


__all__ = [
    "OptimizationError",
    "OptimizationNotFoundError",
    "OptimizationValidationError",
]
