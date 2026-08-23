"""AURA SDK Execution Graph exceptions."""


class ExecutionGraphError(Exception):
    """Base exception for aura_sdk.execution_graph."""


class ExecutionGraphNotFoundError(ExecutionGraphError):
    """Raised when a execution graph resource is missing."""


class ExecutionGraphValidationError(ExecutionGraphError):
    """Raised when a execution graph resource fails validation."""


__all__ = [
    "ExecutionGraphError",
    "ExecutionGraphNotFoundError",
    "ExecutionGraphValidationError",
]
