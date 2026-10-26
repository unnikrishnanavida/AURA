"""Tool domain models: tools, requests, results, and context.

A tool is a controlled executable unit: identity, description, input schema,
capability, permissions, risk profile, timeout, and execution handler.
"""

from __future__ import annotations

import enum
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from aura_agent.contracts.errors import ActionTimeout, ToolExecutionError, ValidationFailure
from aura_agent.contracts.ids import ActionId, AgentId, ExecutionId, GoalId

__all__ = [
    "RiskLevel",
    "ToolContext",
    "ToolHandler",
    "Tool",
    "ToolResult",
    "SchemaField",
    "validate_schema",
]


class RiskLevel(enum.IntEnum):
    """Ordered risk profile for actions and tools."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class ToolContext:
    """Execution context passed to a tool handler."""

    execution_id: ExecutionId
    agent_id: AgentId
    goal_id: GoalId | None = None
    correlation_id: str | None = None


@runtime_checkable
class ToolHandler(Protocol):
    """A callable that performs the tool's work and returns a ``dict``."""

    def __call__(self, inputs: dict[str, Any], *, context: ToolContext) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SchemaField:
    """A single field of a tool's input schema."""

    name: str
    type: type[Any]
    required: bool = True
    description: str = ""
    allowed: tuple[Any, ...] = ()


def validate_schema(
    inputs: dict[str, Any], schema: dict[str, SchemaField]
) -> list[str]:
    """Validate ``inputs`` against ``schema``; return error messages.

    Deterministic and dependency-free: missing required fields, type
    mismatches, disallowed values, and unknown keys are all reported.
    """
    errors: list[str] = []
    for name, spec in schema.items():
        if name not in inputs:
            if spec.required:
                errors.append(f"missing required input {name!r}")
            continue
        value = inputs[name]
        if value is None:
            errors.append(f"input {name!r} may not be None")
            continue
        if not isinstance(value, spec.type):
            errors.append(
                f"input {name!r} must be {getattr(spec.type, '__name__', str(spec.type))}, "
                f"got {type(value).__name__}"
            )
            continue
        if spec.allowed and value not in spec.allowed:
            errors.append(
                f"input {name!r} must be one of {sorted(spec.allowed)!r}, got {value!r}"
            )
    for key in inputs:
        if key not in schema:
            errors.append(f"unexpected input {key!r}")
    return errors
@dataclass(frozen=True)
class Tool:
    """A registered, executable tool."""

    name: str
    description: str
    input_schema: dict[str, SchemaField]
    capability: str
    permissions: tuple[str, ...]
    risk: RiskLevel = RiskLevel.LOW
    timeout_s: float = 30.0
    action_id: ActionId | None = None
    handler: ToolHandler | None = None
    idempotent: bool = False

    def validate_inputs(self, inputs: dict[str, Any]) -> list[str]:
        return validate_schema(inputs, self.input_schema)

    def execute(
        self,
        inputs: dict[str, Any],
        *,
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool with timeout handling and error wrapping.

        Raises:
            ValidationFailure: inputs fail schema validation
            ActionTimeout:     handler exceeds ``timeout_s``
            ToolExecutionError: handler raised or returned no dict output
        """
        errors = self.validate_inputs(inputs)
        if errors:
            raise ValidationFailure(
                f"tool {self.name!r} input validation failed: {'; '.join(errors)}"
            )
        if self.handler is None:
            raise ToolExecutionError(f"tool {self.name!r} has no handler registered")

        started = time.monotonic()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.handler, inputs, context=context)
        try:
            output = future.result(timeout=self.timeout_s)
        except FutureTimeout:
            future.cancel()
            executor.shutdown(wait=False)
            raise ActionTimeout(
                f"tool {self.name!r} exceeded its {self.timeout_s:g}s timeout"
            ) from None
        except Exception as exc:  # noqa: BLE001 - wrapped into domain error
            executor.shutdown(wait=True)
            raise ToolExecutionError(
                f"tool {self.name!r} failed: {exc}",
                details={"tool": self.name, "error_type": type(exc).__name__},
            ) from exc
        executor.shutdown(wait=True)
        duration = time.monotonic() - started
        if not isinstance(output, dict):
            raise ToolExecutionError(
                f"tool {self.name!r} returned non-dict output {type(output).__name__}"
            )
        return ToolResult(
            tool_name=self.name,
            execution_id=context.execution_id,
            success=True,
            output=output,
            duration_s=duration,
        )


@dataclass(frozen=True)
class ToolResult:
    """Structured result of a tool execution."""

    tool_name: str
    execution_id: ExecutionId
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_s: float = 0.0
    resource_usage: dict[str, float] = field(default_factory=dict)
    observed_state: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
