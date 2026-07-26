"""Model-specific exceptions."""

from __future__ import annotations


class ModelError(Exception):
    """Base exception for model failures."""


class ModelConfigurationError(ModelError):
    """Raised when model configuration is invalid."""


class ModelInitializationError(ModelError):
    """Raised when model initialization fails."""


class ModelNotFoundError(ModelError):
    """Raised when a model is not registered or available."""


class ModelUnavailableError(ModelError):
    """Raised when a model cannot be reached."""
