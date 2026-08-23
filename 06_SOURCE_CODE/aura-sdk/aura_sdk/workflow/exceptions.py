"""AURA SDK Workflow exceptions."""


class WorkflowError(Exception):
    """Base exception for aura_sdk.workflow."""


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow resource is missing."""


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow resource fails validation."""


__all__ = [
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
]
