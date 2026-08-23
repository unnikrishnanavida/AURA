"""Tests for memory bridge, telemetry, and loop control."""

from __future__ import annotations

import unittest

from aura_agent.contracts.ids import AgentId, ExecutionId
from aura_agent.loop_control import LoopController, LoopReason
from aura_agent.memory_bridge import (
    Experience,
    InMemoryMemory,
    MemoryBridge,
    MemoryQuery,
)
from aura_agent.telemetry import Telemetry

AGENT = AgentId("ag-mt-1")


class MemoryBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = MemoryBridge(provider=InMemoryMemory())

    def test_write_and_retrieve_experience(self):
        self.memory.write_experience(Experience(action="write", succeeded=True))
        hits = self.memory.retrieve(MemoryQuery(kind="experience"))
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0].entry.metadata["succeeded"])

    def test_retrieval_by_kind_and_key(self):
        self.memory.write_outcome(actor="a1", action="run", succeeded=True)
        self.memory.write_reflection(text="learned x", correlation_id="c1")
        by_kind = self.memory.retrieve(MemoryQuery(kind="reflection"))
        self.assertEqual(len(by_kind), 1)
        by_key = self.memory.retrieve(MemoryQuery(kind="outcome", key="out:run:a1"))
        self.assertEqual(len(by_key), 1)


class LoopControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = LoopController(max_repetitions=3)

    def test_repetition_detected(self):
        for _ in range(3):
            signals = self.controller.record("tool:a")
        self.assertTrue(any(s.reason == LoopReason.REPETITION for s in signals))

    def test_oscillation_detected(self):
        for action in ["a", "b", "a", "b"]:
            self.controller.record(action)
        # last 4 = a,b,a,b => oscillation
        signals = self.controller.record("a")
        self.assertTrue(any(s.reason == LoopReason.OSCILLATION for s in signals))

    def test_no_false_positive_for_distinct_actions(self):
        for action in ["a", "b", "c", "d"]:
            signals = self.controller.record(action)
        self.assertEqual(signals, [])


class TelemetryTests(unittest.TestCase):
    def test_metrics_track_success_rate(self):
        telemetry = Telemetry()
        telemetry.finish_execution(agent_id=str(AGENT), success=True, duration_s=0.1)
        telemetry.finish_execution(agent_id=str(AGENT), success=False, duration_s=0.2)
        snapshot = telemetry.snapshot(str(AGENT))
        self.assertEqual(snapshot["executions"], 2)
        self.assertEqual(snapshot["success_rate"], 0.5)

    def test_increment_counters(self):
        telemetry = Telemetry()
        telemetry.increment(agent_id=str(AGENT), metric="safety_denials")
        telemetry.increment(agent_id=str(AGENT), metric="safety_denials")
        self.assertEqual(
            telemetry.snapshot(str(AGENT))["safety_denials"], 2
        )


if __name__ == "__main__":
    unittest.main()