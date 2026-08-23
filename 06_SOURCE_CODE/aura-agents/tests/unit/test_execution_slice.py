"""Integration test: the guarded execution vertical slice.

Coverage: successful execution, missing capability, permission denied,
approval required, safety denial, budget exhaustion, tool failure, timeout --
all through the real guarded pipeline.
"""

from __future__ import annotations

import unittest

from aura_agent.autonomy import AutonomyEngine, AutonomyMode
from aura_agent.budgets import AgentBudget, BudgetEngine
from aura_agent.capability_discovery import Capability, CapabilityRegistry
from aura_agent.constitution import AgentConstitution
from aura_agent.contracts.errors import (
    ApprovalRequired,
    BudgetExceeded,
    CapabilityDenied,
    PermissionDenied,
    SafetyDenied,
)
from aura_agent.contracts.ids import ActionId, AgentId, ExecutionId, GoalId
from aura_agent.execution_bridge import (
    ExecutionDependencies,
    ExecutionEngine,
    ExecutionRequest,
)
from aura_agent.flight_recorder import AgentFlightRecorder
from aura_agent.policies import Decision, PermissionPolicy, PolicyEngine
from aura_agent.policies.safety import SafetyEvaluator, SafetyPolicy
from aura_agent.tools import Tool, ToolRegistry
from tests.fakes import make_timeout_tool, make_write_tool

AGENT = AgentId("ag-test-001")
GOAL = GoalId("goal-test-001")
class PipelineFactory:
    """Wires a self-contained guarded pipeline."""

    def __init__(self) -> None:
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(make_write_tool())
        self.tool_registry.register(make_timeout_tool())

        self.caps = CapabilityRegistry()
        self.caps.register(Capability(name="filesystem.write"))
        self.caps.register(Capability(name="tools.sleep"))

        self.policies = PolicyEngine()
        self.policies.add_policy(
            PermissionPolicy(
                name="allow-fs",
                effect=Decision.ALLOW,
                action="filesystem.*",
                resource="filesystem.*",
            )
        )
        self.policies.add_policy(
            PermissionPolicy(
                name="allow-sleep",
                effect=Decision.ALLOW,
                action="tools.sleep",
                resource="*",
            )
        )

        self.safety = SafetyEvaluator()
        self.constitution = AgentConstitution()
        self.autonomy = AutonomyEngine(initial_mode=AutonomyMode.SUPERVISED)
        self.budgets = BudgetEngine()
        self.recorder = AgentFlightRecorder()

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
        self.engine = ExecutionEngine(deps=self.deps)

    def request(
        self,
        tool: str,
        capability: str | None = None,
        *,
        risk_score: float = 0.1,
        execution_id: ExecutionId | None = None,
        **inputs: object,
    ) -> ExecutionRequest:
        return ExecutionRequest(
            action_id=ActionId.new(),
            tool_name=tool,
            capability=capability or tool,
            agent_id=AGENT,
            goal_id=GOAL,
            inputs=dict(inputs),
            risk_score=risk_score,
            execution_id=execution_id,
        )
class ExecutionSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = PipelineFactory()

    def test_successful_execution(self):
        result = self.pipeline.engine.execute(
            self.pipeline.request("filesystem.write", path="/tmp/a", content="x")
        )
        self.assertTrue(result.success)
        assert result.primary is not None
        self.assertEqual(result.primary.output["written"], "/tmp/a")
        self.assertEqual(result.state, "succeeded")

    def test_missing_capability_raises(self):
        # tool exists, but the requested capability is not registered
        with self.assertRaises(CapabilityDenied):
            self.pipeline.engine.execute(
                self.pipeline.request(
                    "filesystem.write", capability="database.delete",
                    path="/x", content="y",
                )
            )

    def test_permission_denied_for_denied_action(self):
        self.pipeline.policies.add_policy(
            PermissionPolicy(
                name="deny-sleep",
                effect=Decision.DENY,
                action="tools.sleep",
                resource="*",
            )
        )
        with self.assertRaises(PermissionDenied):
            self.pipeline.engine.execute(self.pipeline.request("tools.sleep"))

    def test_approval_required_at_high_risk(self):
        with self.assertRaises(ApprovalRequired):
            self.pipeline.engine.execute(
                self.pipeline.request(
                    "filesystem.write", path="/x", content="y", risk_score=0.9
                )
            )

    def test_safety_denied_for_forbidden_capability(self):
        self.pipeline.safety.add_policy(
            SafetyPolicy(
                name="no-destructive",
                forbidden_capabilities=frozenset({"filesystem.destructive"}),
            )
        )
        self.pipeline.caps.register(Capability(name="filesystem.destructive"))
        self.pipeline.tool_registry.register(
            Tool(
                name="filesystem.destructive",
                description="destructive",
                input_schema={},
                capability="filesystem.destructive",
                permissions=("filesystem:write",),
                handler=lambda inputs, *, context: {"done": True},
                timeout_s=1,
            )
        )
        with self.assertRaises(SafetyDenied):
            self.pipeline.engine.execute(
                self.pipeline.request(
                    "filesystem.destructive", capability="filesystem.destructive"
                )
            )

    def test_budget_exhaustion_blocks(self):
        execution_id = ExecutionId("exe-budget-1")
        self.pipeline.budgets.attach(execution_id, AgentBudget(limits={"actions": 0.0}))
        with self.assertRaises(BudgetExceeded):
            self.pipeline.engine.execute(
                self.pipeline.request(
                    "filesystem.write", path="/x", content="y",
                    execution_id=execution_id,
                )
            )

    def test_tool_failure_is_reported(self):
        result = self.pipeline.engine.execute(
            self.pipeline.request("filesystem.write", path="/fail", content="y")
        )
        self.assertFalse(result.success)
        self.assertEqual(result.state, "failed")

    def test_timeout_is_reported(self):
        result = self.pipeline.engine.execute(
            self.pipeline.request("tools.sleep", risk_score=0.0)
        )
        self.assertFalse(result.success)
        assert result.primary is not None
        self.assertEqual(result.primary.failure_class.value, "timeout")

    def test_flight_recorder_captures_trajectory(self):
        self.pipeline.engine.execute(
            self.pipeline.request("filesystem.write", path="/rec", content="x")
        )
        events = self.pipeline.recorder.events()
        self.assertTrue(any(e.event_type == "execution.started" for e in events))
        self.assertTrue(any(e.event_type == "execution.succeeded" for e in events))


if __name__ == "__main__":
    unittest.main()
