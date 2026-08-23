"""AURA SDK Prediction exceptions."""


class PredictionError(Exception):
    """Base exception for aura_sdk.prediction."""


class PredictionNotFoundError(PredictionError):
    """Raised when a prediction resource is missing."""


class PredictionValidationError(PredictionError):
    """Raised when a prediction resource fails validation."""


__all__ = [
    "PredictionError",
    "PredictionNotFoundError",
    "PredictionValidationError",
]
