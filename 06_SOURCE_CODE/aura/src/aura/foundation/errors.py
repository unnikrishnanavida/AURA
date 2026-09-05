"""The one AURA domain-error hierarchy.

Every engine raises subclasses of :class:`AuraError` so error handling is
uniform and every error carries a stable machine-readable code.
"""

from __future__ import annotations


class AuraError(Exception):
    """Base class for all AURA domain errors."""

    code = "aura.error"

    def __init__(self, message: str, *, correlation_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.correlation_id = correlation_id

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class ConfigurationError(AuraError):
    code = "config.invalid"


class ValidationError(AuraError):
    code = "validation.failed"


class LifecycleError(AuraError):
    code = "lifecycle.failed"


class InvalidStateTransitionError(AuraError):
    code = "lifecycle.invalid_state"


class NotFoundError(AuraError):
    code = "not_found"


class CapabilityError(AuraError):
    """The actor or request does not satisfy the required capability."""

    code = "capability.missing"


class PermissionDeniedError(AuraError):
    """Policy decision is a hard DENY (not merely approval-required)."""

    code = "permission.denied"


class ApprovalRequiredError(AuraError):
    """Policy decision is APPROVAL_REQUIRED and no approval is present."""

    code = "permission.approval_required"


class SafetyDeniedError(AuraError):
    code = "safety.denied"


class BudgetExhaustedError(AuraError):
    code = "budget.exhausted"


class AuraTimeoutError(AuraError):
    code = "timeout"


class CancelledError(AuraError):
    code = "cancelled"


class RecoveryError(AuraError):
    code = "recovery.failed"


class ToolExecutionError(AuraError):
    code = "tool.execution_failed"


class LoopDetectedError(AuraError):
    code = "loop.detected"


__all__ = [
    "ApprovalRequiredError",
    "AuraError",
    "AuraTimeoutError",
    "BudgetExhaustedError",
    "CancelledError",
    "CapabilityError",
    "ConfigurationError",
    "InvalidStateTransitionError",
    "LifecycleError",
    "LoopDetectedError",
    "NotFoundError",
    "PermissionDeniedError",
    "RecoveryError",
    "SafetyDeniedError",
    "ToolExecutionError",
    "ValidationError",
]