"""AURA SDK Flight Recorder exceptions."""


class FlightRecorderError(Exception):
    """Base exception for aura_sdk.flight_recorder."""


class FlightRecorderNotFoundError(FlightRecorderError):
    """Raised when a flight recorder resource is missing."""


class FlightRecorderValidationError(FlightRecorderError):
    """Raised when a flight recorder resource fails validation."""


__all__ = [
    "FlightRecorderError",
    "FlightRecorderNotFoundError",
    "FlightRecorderValidationError",
]
