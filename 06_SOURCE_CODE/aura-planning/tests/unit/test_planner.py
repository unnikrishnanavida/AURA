"""Behavioral tests for the aura-planning planner.

Covers the required flow: GOAL -> DECOMPOSITION -> CONSTRAINT VALIDATION ->
CANDIDATE PLANS -> CAPABILITY GAP DETECTION -> RISK ANALYSIS -> PLAN
COMPARISON -> SELECTED PLAN -> CONTINGENCY PLAN.

Critical property: the planner must NOT pretend impossible plans are
executable. Unsatisfied constraints, missing capabilities, high risk, and
uncertainty are represented explicitly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_planning.constraints.models.constraint import Constraint
from aura_planning.constraints.models.constraint_set import ConstraintSet
from aura_planning.constraints.models.hard_constraint import HardConstraint
from aura_planning.goals.models.goal import Goal
from aura_planning.planning.planner import ActionSpec, Planner
from aura_planning.plans.plan import Plan


def _goal(objective="achieve X") -> Goal:
    return Goal(goal_id="gl-1", objective=objective, desired_state={"done": True})


def _actions(*ids: str, **cap) -> tuple[ActionSpec, ...]:
    return tuple(
        ActionSpec(
            action_id=action_id,
            capability=cap.get("cap", "domain.execute"),
            risk=float(cap.get("risk", 0.0)),
        )
        for action_id in ids
    )


def test_impossible_constraint_makes_plan_infeasible():
    """A hard constraint that can never be satisfied must NOT produce an
    executable plan."""
    forbidden = HardConstraint(
        constraint=Constraint("no-execute", lambda plan: False, "execution is forbidden")
    )
    planner = Planner(
        goal=_goal(),
        constraints=ConstraintSet(hard=(forbidden,)),
        available_capabilities={"domain.execute"},
    )
    plan = planner.candidates([_actions("a")])[0]
    assert plan.feasible is False
    assert plan.actionable is False
    assert plan.unsatisfied_constraints  # explicit representation
    assert "execution is forbidden" in str(plan.unsatisfied_constraints[0])


def test_missing_capability_is_represented():
    """A plan requiring a capability that is not available must expose it."""
    planner = Planner(
        goal=_goal(),
        available_capabilities={"domain.execute"},  # note: no filesystem.write
    )
    plan = planner.candidates([_actions("write", cap="filesystem.write")])[0]
    assert plan.feasible is False
    assert plan.missing_capabilities
    assert plan.missing_capabilities[0].capability == "filesystem.write"


def test_alternatives_are_generated():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec", "b.exec"})
    candidates = planner.candidates(
        [
            _actions("plan-a", cap="a.exec"),
            _actions("plan-b", cap="b.exec"),
        ]
    )
    assert len(candidates) == 2
    assert {c.actions[0].action_id for c in candidates} == {"plan-a", "plan-b"}


def test_select_prefers_feasible_over_infeasible():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec"})
    feasible = planner.candidates([_actions("ok", cap="a.exec")])[0]
    infeasible = planner.candidates([_actions("bad", cap="missing.cap")])[0]
    selected = planner.select([infeasible, feasible], score_fn=lambda p: 1.0)
    # Even though both would score equally, the feasible plan wins.
    assert selected.actions[0].action_id == "ok"


def test_select_scores_by_custom_fn():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec", "b.exec"})
    low_risk = planner.candidates([_actions("low", cap="a.exec", risk=0.1)])[0]
    high_risk = planner.candidates([_actions("high", cap="b.exec", risk=0.9)])[0]
    selected = planner.select([high_risk, low_risk], score_fn=lambda p: 1.0 - (p.risk.exposure if p.risk else 0))
    assert selected.actions[0].action_id == "low"


def test_high_risk_is_not_actionable():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec"})
    plan = planner.candidates([_actions("risky", cap="a.exec", risk=0.95)])[0]
    assert plan.feasible is True  # capability + constraints OK
    assert plan.actionable is False  # but too risky to execute


def test_uncertainty_is_first_class():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec"})
    unverified = planner.candidates([_actions("u1", cap="a.exec"), _actions("u2", cap="a.exec")])[0]
    assert 0.0 < unverified.uncertainty <= 1.0
    assert "uncertainty" in unverified.to_dict()


def test_contingency_plan_attached():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec", "b.exec"})
    primary = planner.candidates([_actions("primary", cap="a.exec")])[0]
    fallback_plan = planner.candidates([_actions("fallback", cap="b.exec")])[0]
    planner.with_contingency(primary, fallback_plan)
    assert primary.contingency is not None
    assert primary.contingency.actions[0].action_id == "fallback"


def test_replan_after_failure_selects_alternative():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec", "b.exec", "c.exec"})
    original = planner.candidates([_actions("failing", cap="a.exec")])[0]
    alt1 = planner.candidates([_actions("alt-b", cap="b.exec")])[0]
    alt2 = planner.candidates([_actions("alt-c", cap="c.exec")])[0]
    replanned = planner.replan_after_failure(original, failed_action_id="failing", alternatives=[alt1, alt2])
    assert replanned.actions[0].action_id != "failing"
    assert replanned.metadata.get("replanned_after") == "failing"


def test_dependency_cycle_detected():
    """A cyclic dependency graph cannot be scheduled; the planner must not
    pretend it is executable."""
    from aura_planning.dependencies.graph.dependency_edge import DependencyEdge
    from aura_planning.dependencies.graph.dependency_graph import DependencyGraph
    from aura_planning.dependencies.graph.dependency_node import DependencyNode

    graph = DependencyGraph()
    graph.add_node(DependencyNode("a"))
    graph.add_node(DependencyNode("b"))
    graph.add_edge(DependencyEdge("a", "b"))
    graph.add_edge(DependencyEdge("b", "a"))
    try:
        graph.topological_order()
    except ValueError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("cyclic dependency graph must be rejected")


def test_satisfied_dependency_ready():
    from aura_planning.dependencies.graph.dependency_node import DependencyNode

    a = DependencyNode("a")
    a.incoming.add("setup")
    assert a.ready({"setup"}) is True
    assert a.ready(set()) is False
    assert a.ready(set()) is False
    planner = Planner(goal=_goal(), available_capabilities={"a.exec"})
    plan = planner.candidates([_actions("missing-dep", cap="unavailable.cap")])[0]
    payload = plan.to_dict()
def test_plan_to_dict_marks_infeasible_plan():
    planner = Planner(goal=_goal(), available_capabilities={"a.exec"})
    plan = planner.candidates([_actions("missing-dep", cap="unavailable.cap")])[0]
    payload = plan.to_dict()
    assert payload["feasible"] is False
    assert payload["missing_capabilities"]
    assert payload["feasible"] is False
    assert payload["missing_capabilities"]