"""aura-execution — domain execution engine for AURA.

Owns the action lifecycle: capability checks, permission/safety gates,
approval review, budgets, preparation, dispatch, observation, validation,
recovery, and flight-recorded tracing. Security and approval gates are never
bypassed.
"""

from __future__ import annotations

from aura_execution.actions.models.executable_action import ExecutableAction
from aura_execution.capabilities.models.capability import Capability
from aura_execution.contracts.requests.execution_request import ExecutionRequest
from aura_execution.contracts.responses.execution_result import ExecutionResult
from aura_execution.contracts.responses.execution_status import ExecutionStatus
from aura_execution.execution_state.state_engine import StateEngine
from aura_execution.orchestration.execution_engine import ExecutionEngine
from aura_execution.orchestration.orchestrator import Orchestrator
from aura_execution.safety.safety_engine import SafetyDecision, SafetyEngine

__all__ = [
    "Capability",
    "ExecutableAction",
    "ExecutionEngine",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "Orchestrator",
    "SafetyDecision",
    "SafetyEngine",
    "StateEngine",
]