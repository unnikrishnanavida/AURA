"""Planning domain tests: decomposition, validation, risk analysis, alternatives, comparison."""

from __future__ import annotations

import pytest

from aura.foundation.errors import ValidationError
from aura.planning.decomposer import GoalDecomposer
from aura.planning.engine import PlanningEngine
from aura.planning.models import Constraint, Goal, Task
from aura.planning.risk import RiskAnalyzer
from aura.planning.validator import PlanValidator


def make_goal() -> Goal:
    return Goal.create(description="deliver the platform")


def tasks_dep() -> list[Task]:
    return [
        Task(name="build", capability="filesystem.write"),
        Task(name="test", capability="execution.run", prerequisites=("build",)),
        Task(name="ship", capability="deploy", prerequisites=("test",)),
    ]


def test_decomposer_orders_by_dependency() -> None:
    ordered = GoalDecomposer().decompose(make_goal(), tasks_dep())
    names = [t.name for t in ordered]
    assert names.index("build") < names.index("test") < names.index("ship")


def test_decomposer_circular_dependency() -> None:
    tasks = [Task(name="a", prerequisites=("b",)), Task(name="b", prerequisites=("a",))]
    with pytest.raises(ValidationError):
        GoalDecomposer().decompose(make_goal(), tasks)


def test_decomposer_unknown_prerequisite() -> None:
    tasks = [Task(name="a", prerequisites=("ghost",))]
    with pytest.raises(ValidationError):
        GoalDecomposer().decompose(make_goal(), tasks)


def test_validator_accepts_valid_plan() -> None:
    validation = PlanValidator().validate(goal=make_goal(), tasks=tasks_dep())
    assert validation.valid


def test_validator_rejects_empty_tasks() -> None:
    validation = PlanValidator().validate(goal=make_goal(), tasks=[])
    assert not validation.valid


def test_validator_missing_capability() -> None:
    validation = PlanValidator().validate(
        goal=make_goal(),
        tasks=[Task(name="x", capability="secret.capability")],
        requested_capabilities={"approved.only"},
    )
    assert not validation.valid
    assert any("capability" in issue for issue in validation.issues)


def test_risk_analyzer_flags_high_risk() -> None:
    plan_risk = RiskAnalyzer().analyze([Task(name="risky", risk=0.95)])
    assert plan_risk.level in {"high", "medium"}
    assert plan_risk.required_capabilities == ("domain.execute",)


def test_risk_analyzer_empty() -> None:
    plan_risk = RiskAnalyzer().analyze([])
    assert plan_risk.level == "low"


def test_planning_engine_creates_plan() -> None:
    result = PlanningEngine().plan(goal=make_goal(), tasks=tasks_dep())
    assert result.primary is not None
    assert result.primary.names == ["1:build", "2:test", "3:ship"]


def test_planning_engine_validation_failure() -> None:
    result = PlanningEngine().plan(goal=make_goal(), tasks=[])
    assert result.primary is None
    assert result.issues


def test_plan_alternatives_generated() -> None:
    result = PlanningEngine().plan(
        goal=make_goal(),
        tasks=[
            Task(name="a", estimated_cost=1.0),
            Task(name="b", estimated_cost=2.0),
        ],
        max_alternatives=2,
    )
    assert result.primary is not None
    assert len(result.alternatives) <= 2


def test_plan_constraint_forbids_capability() -> None:
    result = PlanningEngine().plan(
        goal=make_goal(),
        tasks=[Task(name="danger", capability="kernel.write")],
        constraints=(Constraint(kind="forbid_capability", value="kernel.write"),),
    )
    assert result.primary is None


def test_goal_create_requires_description() -> None:
    with pytest.raises(ValueError):
        Goal.create(description="  ")