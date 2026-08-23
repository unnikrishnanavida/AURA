"""AURA SDK Pipelines exceptions."""


class PipelineError(Exception):
    """Base exception for aura_sdk.pipelines."""


class PipelineNotFoundError(PipelineError):
    """Raised when a pipelines resource is missing."""


class PipelineValidationError(PipelineError):
    """Raised when a pipelines resource fails validation."""


__all__ = [
    "PipelineError",
    "PipelineNotFoundError",
    "PipelineValidationError",
]
