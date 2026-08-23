"""AURA SDK Digital Twin exceptions."""


class DigitalTwinError(Exception):
    """Base exception for aura_sdk.digital_twin."""


class DigitalTwinNotFoundError(DigitalTwinError):
    """Raised when a digital twin resource is missing."""


class DigitalTwinValidationError(DigitalTwinError):
    """Raised when a digital twin resource fails validation."""


__all__ = [
    "DigitalTwinError",
    "DigitalTwinNotFoundError",
    "DigitalTwinValidationError",
]
