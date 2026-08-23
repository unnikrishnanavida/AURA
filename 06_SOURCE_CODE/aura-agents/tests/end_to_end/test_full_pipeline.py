"""End-to-end scenario tests: the mandated full pipeline and intentional
failure injections through the public DSL where possible.
"""

from __future__ import annotations

import time
import unittest

from aura_agent import dsl
from aura_agent.contracts.errors import (
    ApprovalRequired,
    BudgetExceeded,
    CapabilityDenied,
    PermissionDenied,
)
from aura_agent.contracts.ids import ActionId, ExecutionId
from aura_agent.execution_bridge import ExecutionRequest
from aura_agent.tools import SchemaField, Tool


def make_fs_tool(*, timeout_s: float = 2.0) -> Tool:
    def _handler(inputs, *, context):
        return {"written": inputs["path"], "ok": True, "completed": True}

    return Tool(
        name="filesystem.write",
        description="write a string to a path",
        input_schema={
            "path": SchemaField(name="path", type=str, required=True),
            "content": SchemaField(name="content", type=str, required=True),
        },
        capability="filesystem.write",
        permissions=("filesystem:write",),
        handler=_handler,
        timeout_s=timeout_s,
    )


def make_noop_tool(*, timeout_s: float = 1.0) -> Tool:
    def _handler(inputs, *, context):
        return {"ok": True}

    return Tool(
        name="tools.noop",
        description="a no-input tool used to exercise loop control",
        input_schema={},
        capability="tools.noop",
        permissions=(),
        handler=_handler,
        timeout_s=timeout_s,
    )


def make_slow_tool(*, proc_time_s: float = 0.5, timeout_s: float = 0.1) -> Tool:
    def _handler(inputs, *, context):
        time.sleep(proc_time_s)
        return {"done": True}

    return Tool(
        name="tools.slow",
        description="sleeps past its timeout",
        input_schema={},
        capability="tools.slow",
        permissions=(),
        handler=_handler,
        timeout_s=timeout_s,
    )


class EndToEndScenarioTests(unittest.TestCase):
    def test_successful_goal_completed_via_public_dsl(self):
        agent = (
            dsl.AgentBuilder(name="e2e")
            .with_tool(make_noop_tool())
            .allow(action="tools.*", resource="*")
            .with_capability("tools.noop")
            .build()
        )
        goal = agent.create_goal(
            description="complete a task",
            success_criteria=["ok == True"],
        )
        outcome = agent.run_goal(goal=goal, capabilities=["tools.noop"])
        self.assertTrue(outcome.success, outcome.reason)
        self.assertEqual(
            agent.components.goal_engine.get(goal.id).status.value, "completed"
        )
        # trajectory recorded
        self.assertTrue(agent.components.flight_recorder.events())

    def test_missing_capability_denied(self):
        agent = dsl.AgentBuilder(name="nocap").with_tool(make_fs_tool()).build()
        # capability not declared on the agent -> the tool is registered but the
        # capability gate is not satisfied because the DSL associates the tool
        # capability; request a *different* capability to force a denial.
        with self.assertRaises(CapabilityDenied):
            agent.execute_action(_fs_request(agent, capability="database.delete"))

    def test_permission_denied_without_allow(self):
        agent = dsl.AgentBuilder(name="noperm").with_tool(make_fs_tool()).with_capability("filesystem.write").build()
        with self.assertRaises(PermissionDenied):
            agent.execute_action(_fs_request(agent))

    def test_approval_required_in_manual_mode(self):
        from aura_agent.autonomy import AutonomyMode

        agent = (
            dsl.AgentBuilder(name="manual")
            .with_tool(make_fs_tool())
            .allow(action="filesystem.*", resource="filesystem.*")
            .with_autonomy(AutonomyMode.MANUAL)
            .with_capability("filesystem.write")
            .build()
        )
        with self.assertRaises(ApprovalRequired):
            agent.execute_action(_fs_request(agent))

    def test_budget_exhaustion(self):
        from aura_agent.budgets import AgentBudget

        agent = (
            dsl.AgentBuilder(name="budget")
            .with_tool(make_fs_tool())
            .allow(action="filesystem.*", resource="filesystem.*")
            .with_capability("filesystem.write")
            .build()
        )
        exe = ExecutionId("exe-e2e-budget")
        agent.components.budget_engine.attach(exe, AgentBudget(limits={"actions": 0}))
        with self.assertRaises(BudgetExceeded):
            agent.execute_action(_fs_request(agent, execution_id=exe))

    def test_timeout_reported_not_raised(self):
        agent = (
            dsl.AgentBuilder(name="timeout")
            .with_tool(make_slow_tool())
            .allow(action="tools.*", resource="*")
            .with_capability("tools.slow")
            .build()
        )
        result = agent.execute_action(
            ExecutionRequest(
                action_id=ActionId.new(),
                tool_name="tools.slow",
                capability="tools.slow",
                agent_id=agent.agent_id,
                inputs={},
            )
        )
        self.assertFalse(result.success)
        assert result.primary is not None
        self.assertEqual(result.primary.failure_class.value, "timeout")

    def test_repeated_failure_loop_detection(self):
        # a tool that always *succeeds* with no inputs, but produces no state
        # satisfying the goal criterion -> the loop keeps re-executing the
        # identical step and the loop controller must catch the repetition.
        agent = (
            dsl.AgentBuilder(name="loop")
            .with_tool(make_noop_tool())
            .allow(action="tools.*", resource="*")
            .with_capability("tools.noop")
            .build()
        )
        goal = agent.create_goal(
            description="impossible because criterion never observed",
            success_criteria=["never.observed == True"],
        )
        outcome = agent.run_goal(goal=goal, capabilities=["tools.noop"])
        self.assertFalse(outcome.success)
        self.assertLessEqual(outcome.iterations, 5)
        self.assertTrue("loop detected" in outcome.reason)


if __name__ == "__main__":
    unittest.main()
def _fs_request(agent, *, execution_id=None, capability="filesystem.write") -> ExecutionRequest:
    return ExecutionRequest(
        action_id=ActionId.new(),
        tool_name="filesystem.write",
        capability=capability,
        agent_id=agent.agent_id,
        inputs={"path": "/tmp/e2e", "content": "data"},
        execution_id=execution_id,
    )