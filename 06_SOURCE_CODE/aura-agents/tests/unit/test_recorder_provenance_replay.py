"""Tests for flight recorder, provenance, and replay."""

from __future__ import annotations

import unittest

from aura_agent.contracts.ids import AgentId, ExecutionId
from aura_agent.flight_recorder import AgentFlightRecorder
from aura_agent.flight_recorder.events.agent_event import AgentEvent
from aura_agent.provenance import ProvenanceEngine
from aura_agent.replay import ReplayEngine

AGENT = AgentId("ag-fr-1")
EXECUTION = ExecutionId("exe-fr-1")


class RecorderProvenanceReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recorder = AgentFlightRecorder()
        self.provenance = ProvenanceEngine(self.recorder)
        self.replay = ReplayEngine(self.recorder)

    def _record_events(self) -> None:
        self.recorder.record(
            AgentEvent(
                execution_id=EXECUTION,
                agent_id=AGENT,
                event_type="goal.received",
                payload={"goal": "write file"},
            )
        )
        self.recorder.record(
            AgentEvent(
                execution_id=EXECUTION,
                agent_id=AGENT,
                event_type="capability.verified",
                payload={"capability": "filesystem.write"},
            )
        )
        self.recorder.record(
            AgentEvent(
                execution_id=EXECUTION,
                agent_id=AGENT,
                event_type="execution.succeeded",
                payload={"tool": "filesystem.write", "observed_state": {"written": True}},
            )
        )

    def test_recorder_captures_ordered_trajectory(self):
        self._record_events()
        events = self.recorder.events(str(EXECUTION))
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "goal.received")
        self.assertEqual(events[-1].event_type, "execution.succeeded")

    def test_replay_reconstructs_state(self):
        self._record_events()
        trajectory = self.replay.replay(str(EXECUTION))
        self.assertEqual(trajectory.execution_id, str(EXECUTION))
        self.assertEqual(len(trajectory.steps), 3)
        self.assertEqual(trajectory.reconstructed_state.get("written"), True)
        self.assertEqual(trajectory.event_types[-1], "execution.succeeded")

    def test_provenance_trail_recovers_causal_chain(self):
        self._record_events()
        explanation = self.provenance.explain(str(EXECUTION))
        types = [step["type"] for step in explanation]
        self.assertEqual(types[0], "goal.received")
        self.assertEqual(types[-1], "execution.succeeded")
        # every recorded event appears exactly once in the forward chain
        self.assertEqual(len(types), 3)


if __name__ == "__main__":
    unittest.main()