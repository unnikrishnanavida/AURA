"""Core contracts for the AURA Agent runtime.

This package defines the canonical identifiers, domain exceptions,
execution states, request/result models, and integration interfaces that
the rest of the runtime is built upon.

Public surface:
- :class:`~aura_agent.contracts.ids.AgentId`, ``GoalId``, ``ActionId``, ``ExecutionId``
- :mod:`errors` -- domain exceptions
- :mod:`states` -- execution-state machine
- :mod:`interfaces` -- dependency-injection protocols
- :mod:`requests` / :mod:`results` -- pipeline payload models
"""

from aura_agent.contracts.errors import (
    ActionTimeout,
    ApprovalRequired,
    BudgetExceeded,
    CapabilityDenied,
    ConfigurationError,
    DomainError,
    InvalidStateTransition,
    LoopDetected,
    PermissionDenied,
    RecoveryExhausted,
    SafetyDenied,
    ToolExecutionError,
    ValidationFailure,
)
from aura_agent.contracts.ids import ActionId, AgentId, ExecutionId, GoalId
from aura_agent.contracts.states import ExecutionState, StateMachine, transition_table

__all__ = [
    # ids
    "AgentId",
    "GoalId",
    "ActionId",
    "ExecutionId",
    # errors
    "DomainError",
    "InvalidStateTransition",
    "CapabilityDenied",
    "PermissionDenied",
    "SafetyDenied",
    "ApprovalRequired",
    "BudgetExceeded",
    "ActionTimeout",
    "ToolExecutionError",
    "ValidationFailure",
    "RecoveryExhausted",
    "LoopDetected",
    "ConfigurationError",
    # states
    "ExecutionState",
    "StateMachine",
    "transition_table",
]
