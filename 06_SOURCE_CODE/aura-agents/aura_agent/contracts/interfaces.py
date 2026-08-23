"""Dependency-injection interfaces for the AURA Agent runtime.

Every engine is consumed through a ``Protocol`` so that:
- production implementations can be swapped for fakes in tests,
- sibling AURA engines can be adapted outside this package,
- no component reaches into another component's internals.

These protocols define the *contracts* between domains. Domain-specific
request/result types are imported under ``TYPE_CHECKING`` only to avoid
circular imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from aura_agent.autonomy.modes.autonomy_mode import AutonomyMode
    from aura_agent.budgets.models.agent_budget import AgentBudget
    from aura_agent.budgets.tracking.budget_tracker import BudgetDecision
    from aura_agent.capability_discovery.models import Capability, CapabilityMatch
    from aura_agent.capability_discovery.registry.capability_registry import (
        CapabilityRegistry,
    )
    from aura_agent.constitution.enforcement.enforcement_decision import (
        EnforcementDecision,
    )
    from aura_agent.execution_bridge.requests.execution_request import ExecutionRequest
    from aura_agent.execution_bridge.responses.execution_result import ExecutionResult
    from aura_agent.flight_recorder.events.agent_event import AgentEvent
    from aura_agent.observation.models import Observation
    from aura_agent.policies.models import PermissionDecision, PermissionRequest
    from aura_agent.policies.safety.safety_decision import SafetyDecision
    from aura_agent.policies.safety.safety_evaluator import SafetyEvaluator
    from aura_agent.recovery.recovery_decision import RecoveryDecision, RecoveryRequest
    from aura_agent.tools.models import ToolRequest, ToolResult
    from aura_agent.tools.tool_registry import ToolRegistry


@runtime_checkable
class Recorder(Protocol):
    """Flight recorder contract: everything the runtime may record."""

    def record(self, event: "AgentEvent") -> None: ...
    def events(self, execution_id: str | None = None) -> list["AgentEvent"]: ...


@runtime_checkable
class CapabilityProvider(Protocol):
    """Capability matching contract."""

    def match_capability(self, required: str, *, scopes: list[str] | None = None) -> "CapabilityMatch": ...
    def get_capability(self, name: str) -> "Capability | None": ...
    def register(self, capability: "Capability") -> None: ...


@runtime_checkable
class PermissionEngine(Protocol):
    """Permission (authorization) contract."""

    def evaluate(self, request: "PermissionRequest") -> "PermissionDecision": ...


@runtime_checkable
class SafetyEngine(Protocol):
    """Safety evaluation contract."""

    def evaluate(self, request: "SafetyRequest") -> "SafetyDecision": ...


@runtime_checkable
class ConstitutionChecker(Protocol):
    """Constitution enforcement contract."""

    def check(self, action_name: str, inputs: dict[str, Any]) -> "EnforcementDecision": ...


@runtime_checkable
class AutonomyEngine(Protocol):
    """Autonomy / approval contract."""

    def mode(self) -> "AutonomyMode": ...
    def requires_approval(self, *, risk_score: float, action_name: str) -> bool: ...
    def switch_mode(self, mode: "AutonomyMode") -> None: ...


@runtime_checkable
class BudgetEngine(Protocol):
    """Budget control contract."""

    def check_execution(self, request: "ExecutionRequest", budget: "AgentBudget") -> "BudgetDecision": ...
    def consume(self, execution_id: str, *, time_s: float, cost: float, actions: int = 1) -> None: ...
    def attach(self, execution_id: str, budget: "AgentBudget") -> None: ...
    def acquire(self, execution_id: str) -> "AgentBudget | None": ...


@runtime_checkable
class ToolRegistry(Protocol):
    """Tool lookup contract."""

    def get(self, name: str) -> Any: ...
    def has(self, name: str) -> bool: ...
    def names(self) -> list[str]: ...


@runtime_checkable
class Observer(Protocol):
    """Observation contract: records what actually happened."""

    def observe(self, *, source: str, state: dict[str, Any], signals: list[str] | None = None, execution_id: str | None = None, correlation_id: str | None = None) -> "Observation": ...
    def latest(self, source: str | None = None) -> "Observation | None": ...
    def all(self) -> list["Observation"]: ...


@runtime_checkable
class RecoveryEngine(Protocol):
    """Single-authority recovery contract."""

    def decide(self, request: "RecoveryRequest") -> "RecoveryDecision": ...
    def record_outcome(self, decision: "RecoveryDecision", *, success: bool) -> None: ...


@runtime_checkable
class ReputationStore(Protocol):
    """Reputation scoring contract used by delegation/multi-agent selection."""

    def score(self, agent_id: str) -> dict[str, float]: ...
    def record_outcome(self, agent_id: str, *, success: bool, cost: float = 0.0) -> None: ...


#: `AnyTool` is a placeholder alias to avoid importing the full tool result
#: type in a protocol that only needs symmetric typing. Consumers that need a
#: `ToolResult` should import it directly from ``tools.models``.
AnyTool = Any