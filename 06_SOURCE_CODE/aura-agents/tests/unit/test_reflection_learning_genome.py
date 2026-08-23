"""Tests for reflection, learning, and genome."""

from __future__ import annotations

import unittest

from aura_agent.contracts.ids import AgentId, ExecutionId
from aura_agent.execution_bridge.responses.execution_result import (
    ActionResult,
    ExecutionResult,
)
from aura_agent.genome import AgentGenome, GenomeUpdate, PerformanceEntry
from aura_agent.learning_bridge import LearningBridge, LearningVerdict
from aura_agent.reflection import (
    ImprovementSignal,
    ReflectionEngine,
    ReflectionSeverity,
)

AGENT = AgentId("ag-rl-1")


def _result(success: bool, *, duration: float = 0.2) -> ExecutionResult:
    exe = ExecutionId("exe-reflect-1")
    return ExecutionResult(
        execution_id=exe,
        success=success,
        results=[
            ActionResult(
                execution_id=exe,
                action_id="act-tools.write",
                tool_name="tools.write",
                success=success,
                output={"written": True} if success else {},
                error=None if success else "boom",
                duration_s=duration,
            )
        ],
    )


class ReflectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ReflectionEngine()

    def test_success_reflects_strategy_signal(self):
        reflection = self.engine.reflect(_result(True), agent_id=AGENT)
        types = [s.signal_type for s in reflection.signals]
        self.assertIn("strategy.improvement", types)

    def test_failure_reflects_failure_target(self):
        reflection = self.engine.reflect(_result(False), agent_id=AGENT)
        targets = [str(t.value) for t in reflection.targets]
        self.assertIn("failure", targets)

    def test_safety_relevant_signals_flagged(self):
        risky = ImprovementSignal(
            signal_type="safety.policy_change", target="x", suggestion="raise ceiling"
        )
        self.assertTrue(risky.is_safety_relevant())


class GenomeLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.genome = AgentGenome(AGENT)
        self.learning = LearningBridge(self.genome, authorize_safety_relevant=False)

    def test_validated_learning_applies_to_genome(self):
        signal = ImprovementSignal(
            signal_type="strategy.improvement",
            target="tools.write",
            suggestion="reuse tools.write for identical goals",
            severity=ReflectionSeverity.SUGGESTION,
        )
        verdict = self.learning.ingest(signal, authorized_by="test")
        self.assertEqual(verdict, LearningVerdict.APPLIED)
        self.assertIn("strategy.improvement:tools.write", self.genome.learned_behavior)

    def test_unvalidated_learning_refused(self):
        signal = ImprovementSignal(
            signal_type="strategy.improvement", target="tools.write", suggestion="do it"
        )
        verdict = self.learning.ingest(signal, authorized_by=None)
        self.assertEqual(verdict, LearningVerdict.REFUSED_UNVALIDATED)

    def test_safety_relevant_refused_by_default(self):
        signal = ImprovementSignal(
            signal_type="safety.policy", target="x", suggestion="raise ceiling"
        )
        verdict = self.learning.ingest(signal, authorized_by="test")
        self.assertEqual(verdict, LearningVerdict.REFUSED_SAFETY_RELEVANT)

    def test_success_rate_matches_evidence(self):
        for i in range(10):
            self.genome.record_performance(
                PerformanceEntry(action="a", success=(i % 2 == 0))
            )
        self.assertAlmostEqual(self.genome.success_rate(), 0.5, places=6)

    def test_fingerprint_changes_on_update(self):
        before = self.genome.fingerprint
        self.genome.apply_learned_update(
            GenomeUpdate(authorized_by="test"), behavior_key="b", value="c"
        )
        self.assertNotEqual(before, self.genome.fingerprint)

    def test_fingerprint_is_deterministic(self):
        other = AgentGenome(AGENT)
        self.assertEqual(self.genome.fingerprint, other.fingerprint)

    def test_failure_patterns_tracked(self):
        for _ in range(3):
            self.genome.record_performance(
                PerformanceEntry(action="a", success=False, failure_class="timeout")
            )
        self.assertEqual(self.genome.failure_patterns(), {"timeout": 3})


if __name__ == "__main__":
    unittest.main()