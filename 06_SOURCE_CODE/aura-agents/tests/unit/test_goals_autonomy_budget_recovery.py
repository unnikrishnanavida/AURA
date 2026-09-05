"""Tests for goals, autonomy, budgets, and recovery."""

from __future__ import annotations

import unittest

from aura_agent.autonomy import ApprovalPolicy, AutonomyEngine, AutonomyMode
from aura_agent.budgets import AgentBudget, BudgetEngine
from aura_agent.contracts.errors import InvalidStateTransition, ValidationFailure
from aura_agent.contracts.ids import AgentId, ExecutionId
from aura_agent.execution_bridge.responses.execution_result import FailureClass
from aura_agent.goals import ConflictDetector, GoalConstraint, GoalEngine, GoalStatus
from aura_agent.recovery import RecoveryEngine, RecoveryRequest, RetryPolicy

AGENT = AgentId("ag-unit-2")
EXECUTION = ExecutionId("exe-recovery-1")


class AutonomyTests(unittest.TestCase):
    def test_manual_never_allows(self):
        self.assertTrue(
            ApprovalPolicy().evaluate(mode=AutonomyMode.MANUAL, risk_score=0.0).required
        )

    def test_autonomous_allows_low_risk(self):
        self.assertFalse(
            ApprovalPolicy().evaluate(mode=AutonomyMode.AUTONOMOUS, risk_score=0.3).required
        )

    def test_autonomous_requires_approval_above_ceiling(self):
        self.assertTrue(
            ApprovalPolicy().evaluate(mode=AutonomyMode.AUTONOMOUS, risk_score=0.9).required
        )

    def test_escalation_requires_authorization(self):
        engine = AutonomyEngine(initial_mode=AutonomyMode.MANUAL)
        with self.assertRaises(InvalidStateTransition):
            engine.switch_mode(AutonomyMode.AUTONOMOUS, authorized_by=None)

    def test_deescalation_is_always_allowed(self):
        engine = AutonomyEngine(initial_mode=AutonomyMode.AUTONOMOUS)
class GoalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GoalEngine()

    def test_goal_lifecycle(self):
        goal = self.engine.create_goal(agent_id=AGENT, description="do something")
        self.assertEqual(goal.status.value, "created")
        self.engine.activate(goal.id)
        self.engine.start(goal.id)
        self.engine.mark_completed(goal.id)
        self.assertEqual(self.engine.get(goal.id).status.value, "completed")

    def test_goal_requires_description(self):
        with self.assertRaises(ValidationFailure):
            self.engine.create_goal(agent_id=AGENT, description="   ")

    def test_success_criteria_evaluated_against_world_state(self):
        goal = self.engine.create_goal(
            agent_id=AGENT,
            description="create a file",
            success_criteria=["filesystem.file_created == True"],
        )
        self.assertFalse(self.engine.evaluate_success(goal.id, {}))
        self.assertTrue(
            self.engine.evaluate_success(goal.id, {"filesystem.file_created": True})
        )

    def test_conflict_detection_between_constraints(self):
        engine = GoalEngine()
        stable = engine.create_goal(
            agent_id=AGENT,
            description="stable",
            constraints=[
                GoalConstraint(field="release.channel", allowed=frozenset({"stable"}))
            ],
        )
        beta = engine.create_goal(
            agent_id=AGENT,
            description="beta",
            constraints=[
                GoalConstraint(field="release.channel", allowed=frozenset({"beta"}))
            ],
        )
        self.assertEqual(len(ConflictDetector().detect([stable, beta])), 1)

    def test_decomposition_produces_subgoals_with_dependencies(self):
        from aura_agent.goals.decomposition.goal_decomposer import (
            DecompositionPlan,
            GoalDecomposer,
            SubgoalSpec,
        )

        parent = self.engine.create_goal(agent_id=AGENT, description="parent")
        subgoals = GoalDecomposer().decompose(
            parent,
            DecompositionPlan(
                subgoals=[
                    SubgoalSpec(description="a", depends_on=[], success_criteria=["b == 1"]),
                    SubgoalSpec(description="b", depends_on=[0], success_criteria=["c == 2"]),
                ]
            ),
        )
        self.assertEqual(len(subgoals), 2)
        self.assertEqual(list(subgoals[1].dependencies), [subgoals[0].id])


class BudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.budgets = BudgetEngine()

    def test_check_and_consume_are_bounded(self):
        exe = ExecutionId("exe-budget-2")
        self.budgets.attach(exe, AgentBudget(limits={"actions": 3}))
        self.assertTrue(self.budgets.check_execution(exe, projection={"actions": 1}).allowed)
        self.budgets.consume(exe, dimension="actions", amount=1)
        self.budgets.consume(exe, dimension="actions", amount=1)
        # 2 consumed + 1 projected == 3 limit -> still allowed
        self.assertTrue(self.budgets.check_execution(exe, projection={"actions": 1}).allowed)
        # 2 consumed + 2 projected == 4 > 3 limit -> denied
        self.assertFalse(self.budgets.check_execution(exe, projection={"actions": 2}).allowed)
        # consuming beyond the limit raises
        with self.assertRaises(Exception):
            self.budgets.consume(exe, dimension="actions", amount=2)

    def test_negative_consumption_rejected(self):
        exe = ExecutionId("exe-budget-neg")
        self.budgets.attach(exe, AgentBudget(limits={"actions": 5}))
        with self.assertRaises(ValueError):
            self.budgets.consume(exe, dimension="actions", amount=-1)


class RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recovery = RecoveryEngine()

    def _request(self, failure_class: FailureClass, attempts: int = 0) -> RecoveryRequest:
        return RecoveryRequest(
            execution_id=EXECUTION,
            goal_id=None,
            tool_name="tools.noop",
            failure_class=failure_class,
            attempts=attempts,
            retry_policy=RetryPolicy(max_retries=2, backoff_s=0.0),
        )

    def test_transient_retries_within_budget(self):
        decision = self.recovery.decide(self._request(FailureClass.TRANSIENT, attempts=0))
        self.assertTrue(decision.should_retry)
        self.assertEqual(decision.strategy.value, "retry")

    def test_transient_aborts_when_retries_exhausted(self):
        decision = self.recovery.decide(self._request(FailureClass.TRANSIENT, attempts=2))
        self.assertFalse(decision.should_retry)
        self.assertEqual(decision.strategy.value, "abort")

    def test_policy_failure_never_retries(self):
        decision = self.recovery.decide(self._request(FailureClass.POLICY))
        self.assertEqual(decision.strategy.value, "abort")

    def test_state_mismatch_rolls_back_then_replans(self):
        first = self.recovery.decide(self._request(FailureClass.STATE_MISMATCH, attempts=0))
        self.assertEqual(first.strategy.value, "rollback")
        second = self.recovery.decide(self._request(FailureClass.STATE_MISMATCH, attempts=1))
        self.assertEqual(second.strategy.value, "replan")

    def test_resource_escalates(self):
        decision = self.recovery.decide(self._request(FailureClass.RESOURCE))
        self.assertEqual(decision.strategy.value, "escalate")


if __name__ == "__main__":
    unittest.main()
