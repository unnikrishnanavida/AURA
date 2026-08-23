"""Unit tests for the core contracts (ids, errors, states)."""

from __future__ import annotations

import unittest

from aura_agent.contracts.errors import (
    InvalidStateTransition,
    SafetyDenied,
)
from aura_agent.contracts.ids import ActionId, AgentId, ExecutionId, GoalId
from aura_agent.contracts.states import ExecutionState, StateMachine


class IdTests(unittest.TestCase):
    def test_new_ids_have_namespaced_prefixes(self):
        self.assertTrue(str(AgentId.new()).startswith("ag-"))
        self.assertTrue(str(GoalId.new()).startswith("goal-"))
        self.assertTrue(str(ActionId.new()).startswith("act-"))
        self.assertTrue(str(ExecutionId.new()).startswith("exe-"))

    def test_ids_are_immutable_strings(self):
        aid = AgentId("ag-abcdef")
        self.assertEqual(str(aid), "ag-abcdef")
        self.assertEqual(aid, "ag-abcdef")

    def test_mismatched_namespace_raises(self):
        with self.assertRaises(ValueError):
            AgentId("goal-wrong")  # noqa: F841

    def test_equality_across_namespaces_never_confuses(self):
        self.assertNotEqual(AgentId("ag-1"), GoalId("goal-1"))


class StateMachineTests(unittest.TestCase):
    def test_valid_success_transition(self):
        sm = StateMachine()
        sm.transition(ExecutionState.READY)
        sm.transition(ExecutionState.RUNNING)
        sm.transition(ExecutionState.SUCCEEDED)
        self.assertTrue(sm.is_terminal)
        self.assertEqual(len(sm.history), 3)

    def test_invalid_transition_raises(self):
        sm = StateMachine(ExecutionState.SUCCEEDED)
        with self.assertRaises(InvalidStateTransition):
            sm.transition(ExecutionState.RUNNING)

    def test_terminal_states_have_no_outgoing(self):
        for terminal in (
            ExecutionState.SUCCEEDED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.ROLLED_BACK,
        ):
            sm = StateMachine(terminal)
            for target in ExecutionState:
                self.assertFalse(sm.can_transition(target))


class DomainErrorTests(unittest.TestCase):
    def test_domain_error_has_message_and_details(self):
        err = SafetyDenied("nope", details={"risk": 0.9})
        self.assertEqual(err.message, "nope")
        self.assertEqual(err.details, {"risk": 0.9})


if __name__ == "__main__":
    unittest.main()