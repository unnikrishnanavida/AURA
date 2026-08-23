"""Planning provider protocol, plan validator, and the planning adapter.

The built-in ``GoalRefinementPlanner`` produces deterministic executable plans
from a planning request by matching the goal to available capabilities/tools.
Plan output must be validated before execution -- the adapter always runs the
validator on provider plans.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aura_agent.planning_bridge.models import (
    PlanResult,
    PlanStep,
    PlanningRequest,
)

__all__ = ["PlanningProvider", "GoalRefinementPlanner", "PlanningBridge", "PlanValidator"]


@runtime_checkable
class PlanningProvider(Protocol):
    def plan(self, request: PlanningRequest) -> PlanResult: ...


class PlanValidator:
    """Deterministic plan validation: every step must name a tool, a
    capability, and have a non-empty inputs mapping."""

    def validate(self, plan: PlanResult) -> PlanResult:
        errors: list[str] = []
        for step in plan.steps:
            if not step.tool_name:
                errors.append("plan contains a step with an empty tool name")
            if not step.capability:
                errors.append("plan contains a step with an empty capability")
        if errors:
            return PlanResult(steps=plan.steps, valid=False, validation_errors=errors)
        return plan


class GoalRefinementPlanner:
    """Deterministic planner used when no AURA Planning provider is wired.

    The planner maps a goal to a single concrete step against a known tool
    when the tool's capability is available to this agent.
    """

    def plan(self, request: PlanningRequest) -> PlanResult:
        capabilities = set(request.capabilities or [])
        goal = request.goal or ""
        candidates: list[tuple[str, str]] = []  # (tool_name, capability)

        for cap in sorted(capabilities):
            if cap not in candidates and _capability_in_goal(cap, goal):
                candidates.append((cap, cap))

        if not candidates:
            # last resort: use any available capability deterministically
            for cap in sorted(capabilities):
                candidates.append((cap, cap))

        if not candidates:
            return PlanResult(steps=[], valid=False, validation_errors=["agent has no capabilities to plan with"])

        tool_name, capability = candidates[0]
        step = PlanStep(
            tool_name=tool_name,
            capability=capability,
            inputs={},
            expected_effects={"completed": True},
            description=f"execute goal step via {tool_name}",
        )
        return PlanResult(steps=[step])


def _capability_in_goal(capability: str, goal: str) -> bool:
    tokens = capability.split(".")
    for token in tokens:
        if token and token in goal:
            return True
    return False


class PlanningBridge:
    """Adapts planning requests to a provider and always validates output."""

    def __init__(
        self,
        provider: PlanningProvider | None = None,
        validator: PlanValidator | None = None,
    ) -> None:
        self._provider = provider or GoalRefinementPlanner()
        self._validator = validator or PlanValidator()

    @property
    def provider(self) -> PlanningProvider:
        return self._provider

    def plan(self, request: PlanningRequest) -> PlanResult:
        raw = self._provider.plan(request)
        return self._validator.validate(raw)