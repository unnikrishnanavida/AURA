"""Planning bridge models: plan requests and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_agent.contracts.ids import AgentId, GoalId

__all__ = ["PlanningRequest", "PlanStep", "PlanResult", "ReplanningResult"]


@dataclass(frozen=True)
class PlanningRequest:
    """A request for a plan.

    ``goal`` is the goal description; ``world_state`` is the *observed* state
    (never conflated with action inputs); ``capabilities`` lists what the
    agent can do; ``constraints``/``budget`` bound the plan.
    """

    goal: str
    goal_id: GoalId
    agent_id: AgentId
    world_state: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    budget: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    """One step in a generated plan."""

    tool_name: str
    capability: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_effects: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class PlanResult:
    """A validated plan ready for execution."""

    steps: list[PlanStep]
    valid: bool = True
    validation_errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReplanningResult:
    """The output of replanning after a recovery decision."""

    plan: PlanResult
    reason: str
