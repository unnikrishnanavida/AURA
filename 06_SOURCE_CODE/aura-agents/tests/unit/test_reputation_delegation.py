"""Tests for reputation scoring and delegation."""

from __future__ import annotations

import unittest

from aura_agent.capability_discovery.registry.agent_registry import (
    AgentCapabilityRegistry,
)
from aura_agent.contracts.ids import AgentId
from aura_agent.delegation import DelegationEngine, TaskRequirements
from aura_agent.reputation import AgentOutcome, ReputationLedger, ReputationScorer

AGENT = AgentId("ag-orch-1")
WORKER_A = AgentId("ag-worker-a")
WORKER_B = AgentId("ag-worker-b")


class ReputationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = ReputationLedger()
        self.scorer = ReputationScorer(self.ledger)

    def test_reputation_from_evidence(self):
        for _ in range(5):
            self.ledger.record(
                AgentOutcome(agent_id=WORKER_A, action="t", success=True)
            )
        for _ in range(5):
            self.ledger.record(
                AgentOutcome(agent_id=WORKER_B, action="t", success=False)
            )
        self.assertGreater(
            self.scorer.score(WORKER_A).success_rate,
            self.scorer.score(WORKER_B).success_rate,
        )

    def test_no_evidence_zero_outcomes(self):
        score = self.scorer.score(AgentId("ag-unknown"))
        self.assertEqual(score.total_outcomes, 0)
        self.assertEqual(score.confidence, 0.0)

    def test_confidence_saturates_with_evidence(self):
        for _ in range(25):
            self.ledger.record(
                AgentOutcome(agent_id=WORKER_A, action="t", success=True)
            )
        self.assertEqual(self.scorer.score(WORKER_A).confidence, 1.0)


class DelegationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.caps = AgentCapabilityRegistry()
        self.delegation = DelegationEngine(
            capabilities=self.caps, reputation=ReputationScorer(ReputationLedger())
        )
        self.caps.register(WORKER_A, {"filesystem.write"}, available=True)
        self.caps.register(WORKER_B, {"filesystem.read"}, available=True)

    def test_selects_worker_with_matching_capability(self):
        task = self.delegation.create_task(
            task_id="task-1",
            delegator=AGENT,
            requirements=TaskRequirements(
                required_capabilities=("filesystem.write",)
            ),
        )
        worker = self.delegation.select_worker(
            task_id=task.task_id, requirements=task.requirements
        )
        self.assertEqual(worker, WORKER_A)

    def test_worker_without_capability_not_proposed(self):
        task = self.delegation.create_task(
            task_id="task-2",
            delegator=AGENT,
            requirements=TaskRequirements(
                required_capabilities=("database.delete",)
            ),
        )
        proposal = self.delegation.propose(
            task_id=task.task_id, worker=WORKER_A
        )
        self.assertIsNone(proposal)

    def test_agreement_lifecycle(self):
        task = self.delegation.create_task(
            task_id="task-3",
            delegator=AGENT,
            requirements=TaskRequirements(
                required_capabilities=("filesystem.read",)
            ),
        )
        self.delegation.agree(task_id=task.task_id, worker=WORKER_B)
        self.delegation.start(task_id=task.task_id)
        self.delegation.complete(task_id=task.task_id, success=True)
        self.assertEqual(
            self.delegation.get(task.task_id).status.value, "completed"
        )


if __name__ == "__main__":
    unittest.main()