"""AURA SDK Orchestration exceptions."""


class OrchestrationError(Exception):
    """Base exception for aura_sdk.orchestration."""


class OrchestrationNotFoundError(OrchestrationError):
    """Raised when a orchestration resource is missing."""


class OrchestrationValidationError(OrchestrationError):
    """Raised when a orchestration resource fails validation."""


__all__ = [
    "OrchestrationError",
    "OrchestrationNotFoundError",
    "OrchestrationValidationError",
]
