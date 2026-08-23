"""Execution bridge: requests, results, and the guarded execution engine."""

from aura_agent.execution_bridge.execution_engine import (
    ExecutionDependencies,
    ExecutionEngine,
)
from aura_agent.execution_bridge.requests.execution_request import ExecutionRequest
from aura_agent.execution_bridge.responses.execution_result import (
    ActionResult,
    ExecutionResult,
    FailureClass,
)

__all__ = [
    "ExecutionRequest",
    "ExecutionResult",
    "ActionResult",
    "FailureClass",
    "ExecutionEngine",
    "ExecutionDependencies",
]