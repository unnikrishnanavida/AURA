"""Unit tests for the cognitive loop (bounded, goal-directed)."""

from __future__ import annotations

import unittest

from aura_agent.autonomy import AutonomyEngine, AutonomyMode
from aura_agent.budgets import BudgetEngine
from aura_agent.capability_discovery import Capability, CapabilityRegistry
from aura_agent.cognitive_loop import CognitiveLoop, CognitiveLoopSettings
from aura_agent.constitution import AgentConstitution
from aura_agent.contracts.ids import AgentId, GoalId
from aura_agent.evaluation import EvaluationEngine
from aura_agent.execution_bridge import ExecutionDependencies, ExecutionEngine
from aura_agent.flight_recorder import AgentFlightRecorder
from aura_agent.goals import GoalEngine
from aura_agent.loop_control import LoopController
from aura_agent.observation import ObservationEngine
from aura_agent.policies import Decision, PermissionPolicy, PolicyEngine
from aura_agent.policies.safety import SafetyEvaluator
from aura_agent.planning_bridge import GoalRefinementPlanner, PlanningBridge
from aura_agent.reasoning_bridge import ReasoningBridge
from aura_agent.recovery import RecoveryEngine
from aura_agent.tools import Tool, ToolRegistry

AGENT = AgentId("ag-loop-1")


def make_noop_tool() -> Tool:
    """A tool with no required inputs so the planner can always bind it."""

    def _handler(_inputs, *, context) -> dict:
        return {"done": True}

    return Tool(
        name="tools.noop",
        description="no-op tool for loop tests",
        input_schema={},
        capability="tools.noop",
        permissions=(),
        handler=_handler,
        timeout_s=1,
    )


class LoopGoalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(make_noop_tool())

        self.caps = CapabilityRegistry()
        self.caps.register(Capability(name="tools.noop"))

        self.policies = PolicyEngine()
        self.policies.add_policy(
            PermissionPolicy(
                name="allow-tools",
                effect=Decision.ALLOW,
                action="tools.*",
                resource="*",
            )
        )
        self.safety = SafetyEvaluator()
        self.constitution = AgentConstitution()
        self.autonomy = AutonomyEngine(initial_mode=AutonomyMode.SUPERVISED)
        self.budgets = BudgetEngine()
        self.recorder = AgentFlightRecorder()
        self.recovery = RecoveryEngine()
        self.loop_controller = LoopController(max_repetitions=3)
        self.observation = ObservationEngine()
        self.evaluation = EvaluationEngine()
        self.goal_engine = GoalEngine()

        self.deps = ExecutionDependencies(
            tool_registry=self.tool_registry,
            capability_registry=self.caps,
            policy_engine=self.policies,
            constitution_checker=self.constitution,
            safety_evaluator=self.safety,
            autonomy_engine=self.autonomy,
            budget_engine=self.budgets,
            recorder=self.recorder,
        )
        self.loop = CognitiveLoop(
            execution_engine=ExecutionEngine(deps=self.deps),
            planning_bridge=PlanningBridge(provider=GoalRefinementPlanner()),
            reasoning_bridge=ReasoningBridge(),
            observation_engine=self.observation,
            evaluation_engine=self.evaluation,
            recovery_engine=self.recovery,
            loop_controller=self.loop_controller,
            recorder=self.recorder,
            goal_engine=self.goal_engine,
            settings=CognitiveLoopSettings(max_iterations=5, max_retries_per_step=1),
        )

    def _goal(self, criterion: str = "completed == True") -> GoalId:
        goal = self.goal_engine.create_goal(
            agent_id=AGENT,
            description="complete the task",
            success_criteria=[criterion],
        )
        self.goal_engine.activate(goal.id)
        return goal.id

    def test_goal_achieved_through_full_cycle(self):
        goal_id = self._goal()
        outcome = self.loop.run(
            goal_id=goal_id,
            agent_id=AGENT,
            goal_description="complete the task",
            world_state={},
            capabilities=["tools.noop"],
        )
        self.assertTrue(outcome.success, outcome.reason)
        self.assertEqual(self.goal_engine.get(goal_id).status.value, "completed")

    def test_loop_terminates_bounded(self) -> None:
        # remove execution capability => the planner has nothing and the loop
        # must terminate cleanly instead of spinning forever
        self.caps.unregister("tools.noop")
        goal_id = self._goal()
        outcome = self.loop.run(
            goal_id=goal_id,
            agent_id=AGENT,
            goal_description="complete the task",
            world_state={},
            capabilities=["tools.noop"],
        )
        self.assertLessEqual(outcome.iterations, 5)


if __name__ == "__main__":
    unittest.main()