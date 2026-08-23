"""AURA SDK Visualization exceptions."""


class VisualizationError(Exception):
    """Base exception for aura_sdk.visualization."""


class VisualizationNotFoundError(VisualizationError):
    """Raised when a visualization resource is missing."""


class VisualizationValidationError(VisualizationError):
    """Raised when a visualization resource fails validation."""


__all__ = [
    "VisualizationError",
    "VisualizationNotFoundError",
    "VisualizationValidationError",
]
