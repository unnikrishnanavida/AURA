"""Domain exceptions for the AURA Agent runtime.

Every subsystem signals failure through a typed exception derived from
:class:`DomainError`. Callers can therefore catch precisely the failure they
care about and are never forced to swallow bare ``Exception``.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "DomainError",
    "ConfigurationError",
    "InvalidStateTransition",
    "CapabilityDenied",
    "PermissionDenied",
    "SafetyDenied",
    "ConstitutionViolation",
    "ApprovalRequired",
    "BudgetExceeded",
    "ActionTimeout",
    "ToolExecutionError",
    "ValidationFailure",
    "RecoveryExhausted",
    "LoopDetected",
    "AgentNotReady",
]


class DomainError(Exception):
    """Base class for all AURA Agent domain exceptions."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __reduce__(self):  # make it picklable for telemetry/flight-recorder
        return (type(self), (self.message,), {"details": self.details})


class ConfigurationError(DomainError):
    """Configuration is invalid, incomplete, or self-contradictory."""


class InvalidStateTransition(DomainError):
    """An execution attempted to move between incompatible states."""

    def __init__(
        self, current: str, target: str, *, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            f"Invalid state transition {current!r} -> {target!r}", details=details
        )
        self.current = current
        self.target = target


class CapabilityDenied(DomainError):
    """The required capability is not registered, enabled, or in scope."""


class PermissionDenied(DomainError):
    """The actor is not authorized for this operation."""


class SafetyDenied(DomainError):
    """A safety policy forbids the operation."""


class ConstitutionViolation(DomainError):
    """The operation violates the agent constitution."""


class ApprovalRequired(DomainError):
    """The operation requires human/controller approval before execution."""


class BudgetExceeded(DomainError):
    """A resource, time, or cost budget has been exhausted."""


class ActionTimeout(DomainError):
    """An action exceeded its allowed execution time."""


class ToolExecutionError(DomainError):
    """A tool raised an error or produced an unusable result."""


class ValidationFailure(DomainError):
    """A request, plan, or result failed input validation."""


class RecoveryExhausted(DomainError):
    """All configured recovery strategies were exhausted without success."""


class LoopDetected(DomainError):
    """The cognitive loop detected repetition, oscillation, or stagnation."""


class AgentNotReady(DomainError):
    """An operation was attempted before the agent runtime was ready."""
