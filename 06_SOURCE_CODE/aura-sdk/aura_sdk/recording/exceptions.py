"""AURA SDK Recording exceptions."""


class RecordingError(Exception):
    """Base exception for aura_sdk.recording."""


class RecordingNotFoundError(RecordingError):
    """Raised when a recording resource is missing."""


class RecordingValidationError(RecordingError):
    """Raised when a recording resource fails validation."""


__all__ = [
    "RecordingError",
    "RecordingNotFoundError",
    "RecordingValidationError",
]
