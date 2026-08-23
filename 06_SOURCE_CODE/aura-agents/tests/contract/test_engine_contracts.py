"""AURA cross-engine contract tests.

These validate the boundaries the Agent engine exposes to other AURA engines
(Core, Reasoning, Memory, Learning, SDK). Because sibling engines may not be
installed in this environment, the contracts are exercised through the
interfaces/protocols this package defines -- future engine implementations
that satisfy the protocol should not silently break the agent.
"""

from __future__ import annotations

import unittest

from aura_agent.contracts.ids import AgentId, ExecutionId, GoalId
from aura_agent.execution_bridge.responses.execution_result import ExecutionResult
from aura_agent.learning_bridge import LearningBridge
from aura_agent.memory_bridge import (
    InMemoryMemory,
    MemoryBridge,
    MemoryQuery,
)
from aura_agent.planning_bridge import PlanResult, PlanStep, PlanningRequest
from aura_agent.reasoning_bridge import ReasoningBridge, ReasoningRequest, ReasoningResult
from aura_agent.reflection import ImprovementSignal

AGENT = AgentId("ag-contract-1")
GOAL = GoalId("goal-contract-1")


class ReasoningContractTests(unittest.TestCase):
    """Agent <-> AURA Reasoning contract."""

    def test_request_structure(self):
        request = ReasoningRequest(
            objective="decide next action",
            context={"risk_score": 0.2},
            constraints=["cost < 5"],
        )
        self.assertEqual(request.objective, "decide next action")
        self.assertIn("risk_score", request.context)

    def test_result_structure_and_confidence_norm(self):
        bridge = ReasoningBridge()

        class FakeProvider:
            def reason(self, req):
                return ReasoningResult(
                    answer="proceed", confidence=1.4, provider="fake"
                )

        bridge._provider = FakeProvider()
        norm = bridge.reason(ReasoningRequest(objective="risk?"))
class PlanningContractTests(unittest.TestCase):
    """The Agent <-> AURA Planning contract (validated before execution)."""

    def test_plan_request_structure(self):
        request = PlanningRequest(
            goal="write a file",
            goal_id=GOAL,
            agent_id=AGENT,
            world_state={"file_exists": False},
            capabilities=["filesystem.write"],
        )
        self.assertFalse(request.world_state["file_exists"])

    def test_plan_result_validation_rejects_bad_steps(self):
        from aura_agent.planning_bridge import PlanValidator

        validator = PlanValidator()
        result = validator.validate(
            PlanResult(
                steps=[PlanStep(tool_name="", capability="filesystem.write", inputs={})]
            )
        )
        self.assertFalse(result.valid)
        self.assertTrue(result.validation_errors)


class MemoryContractTests(unittest.TestCase):
    """Agent <-> AURA Memory contract."""

    def setUp(self) -> None:
        self.memory = MemoryBridge(provider=InMemoryMemory())

    def test_experience_write_and_retrieve(self):
        from aura_agent.memory_bridge import Experience

        self.memory.write_experience(
            Experience(action="fs.write", succeeded=True), correlation_id="c-1"
        )
        records = self.memory.retrieve(MemoryQuery(kind="experience", limit=5))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].entry.kind, "experience")

    def test_outcome_write_contract(self):
        self.memory.write_outcome(actor="ag-x", action="run", succeeded=False)
        hits = self.memory.retrieve(MemoryQuery(kind="outcome"))
        self.assertEqual(len(hits), 1)
        self.assertFalse(hits[0].entry.content["succeeded"])


class LearningContractTests(unittest.TestCase):
    """Agent <-> Learning contract: only validated signals update the genome."""

    def test_safety_relevant_refused_at_boundary(self):
        from aura_agent.genome import AgentGenome

        genome = AgentGenome(AGENT)
        bridge = LearningBridge(genome, authorize_safety_relevant=False)
        signal = ImprovementSignal(
            signal_type="safety.policy_change", target="x", suggestion="relax"
        )
        verdict = bridge.ingest(signal, authorized_by="controller")
        self.assertEqual(verdict, "refused_safety_relevant")


class SDKContractTests(unittest.TestCase):
    """Agent <-> SDK contract: stable public API surface."""

    def test_public_dsl_builds_runtime(self):
        from aura_agent import dsl

        agent = dsl.default_agent(name="contract-sdk")
        self.assertTrue(str(agent.agent_id).startswith("ag-"))
        self.assertEqual(agent.identity.name, "contract-sdk")


class ExecutionResultContractTests(unittest.TestCase):
    """Execution result must carry the fields consumers rely on."""

    def test_execution_result_shape(self):
        exe = ExecutionId("exe-contract-1")
        result = ExecutionResult(
            execution_id=exe, success=True, state="succeeded"
        )
        self.assertEqual(result.execution_id, exe)
        self.assertTrue(result.success)
        self.assertEqual(result.state, "succeeded")


