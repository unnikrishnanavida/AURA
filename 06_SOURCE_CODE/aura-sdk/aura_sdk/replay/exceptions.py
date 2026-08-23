"""AURA SDK Replay exceptions."""


class ReplayError(Exception):
    """Base exception for aura_sdk.replay."""


class ReplayNotFoundError(ReplayError):
    """Raised when a replay resource is missing."""


class ReplayValidationError(ReplayError):
    """Raised when a replay resource fails validation."""


__all__ = [
    "ReplayError",
    "ReplayNotFoundError",
    "ReplayValidationError",
]
