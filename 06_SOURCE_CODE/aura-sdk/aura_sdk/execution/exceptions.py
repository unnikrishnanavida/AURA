"""AURA SDK Execution exceptions."""


class ExecutionError(Exception):
    """Base exception for aura_sdk.execution."""


class ExecutionNotFoundError(ExecutionError):
    """Raised when a execution resource is missing."""


class ExecutionValidationError(ExecutionError):
    """Raised when a execution resource fails validation."""


__all__ = [
    "ExecutionError",
    "ExecutionNotFoundError",
    "ExecutionValidationError",
]
