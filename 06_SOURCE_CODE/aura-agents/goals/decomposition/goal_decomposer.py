"""Goal decomposition into meaningful, ordered subgoals.

Decomposition is deterministic: a goal declares an optional *decomposition
plan* in its metadata (``plan``), expressed as a list of sub-goal
descriptions with explicit preconditions. The decomposer validates the plan
against a capability set and produces ``Goal`` instances with a defined
dependency order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_agent.contracts.ids import GoalId
from aura_agent.goals.models.goal import Goal, GoalConstraint, SuccessCriterion

__all__ = ["GoalDecomposer", "DecompositionPlan", "SubgoalSpec"]


@dataclass(frozen=True)
class SubgoalSpec:
    """One step in a deterministic decomposition plan."""

    description: str
    requires: list[str] = field(default_factory=list)  # capability names
    depends_on: list[int] = field(default_factory=list)  # zero-based indices
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[tuple[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DecompositionPlan:
    """A validated decomposition plan for a goal."""

    subgoals: list[SubgoalSpec]

    def validate(self) -> None:
        """Validate index references and detect dependency cycles."""
        n = len(self.subgoals)
        for i, spec in enumerate(self.subgoals):
            for dep in spec.depends_on:
                if not 0 <= dep < n:
                    raise ValueError(f"subgoal {i} depends on invalid index {dep}")
        # cycle detection over the dependency graph
        visited: list[int] = []
        stack: set[int] = set()

        def visit(node: int) -> None:
            if node in stack:
                raise ValueError(f"cyclic decomposition at subgoal {node}")
            if node in visited:
                return
            stack.add(node)
            for dep in self.subgoals[node].depends_on:
                visit(dep)
            stack.discard(node)
            visited.append(node)

        for i in range(n):
            visit(i)


class GoalDecomposer:
    """Creates subgoals from a validated plan, or a single-step plan when no
    plan is supplied.

    The decomposer is a pure function over domain objects: it does not talk to
    engines, does not execute anything, and is fully deterministic.
    """

    def decompose(self, goal: Goal, plan: DecompositionPlan) -> list[Goal]:
        """Expand ``goal`` into subgoals implementing ``plan``."""
        plan.validate()
        subgoals: list[Goal] = []
        by_index: dict[int, Goal] = {}
        for i, spec in enumerate(plan.subgoals):
            sub = Goal(
                id=GoalId.new(),
                agent_id=goal.agent_id,
                description=spec.description,
                priority=goal.priority,
                parent_id=goal.id,
                dependencies=[
                    by_index[dep].id for dep in spec.depends_on if dep in by_index
                ],
                success_criteria=[
                    SuccessCriterion(condition=c) for c in spec.success_criteria
                ],
                constraints=[
                    GoalConstraint(field=path, allowed=frozenset([value]))
                    for path, value in spec.constraints
                ],
                metadata={
                    "requires_capabilities": spec.requires,
                    "decomposition_slot": i,
                },
            )
            by_index[i] = sub
            subgoals.append(sub)
        goal.subgoals = [s.id for s in subgoals]
        goal.touch()
        return subgoals

    def single_step(self, goal: Goal, capability: str) -> list[Goal]:
        """Decompose into a single subgoal requiring ``capability``."""
        return self.decompose(
            goal,
            DecompositionPlan(
                subgoals=[
                    SubgoalSpec(
                        description=goal.description,
                        requires=[capability],
                        success_criteria=[
                            c.condition for c in goal.success_criteria
                        ],
                    )
                ]
            ),
        )
