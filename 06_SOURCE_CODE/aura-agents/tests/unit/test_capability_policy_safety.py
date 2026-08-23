"""Tests for capability matching, permissions, safety, and constitution."""

from __future__ import annotations

import unittest

from aura_agent.capability_discovery import Capability, CapabilityRegistry, MatchStatus
from aura_agent.constitution import (
    AgentConstitution,
    EnforcementVerdict,
    Principle,
    PrincipleCategory,
)
from aura_agent.contracts.ids import AgentId
from aura_agent.policies import (
    Decision,
    PermissionPolicy,
    PermissionRequest,
    PolicyEngine,
)
from aura_agent.policies.safety import (
    SafetyDecisionValue,
    SafetyEvaluator,
    SafetyPolicy,
    SafetyRequest,
)

AGENT = AgentId("ag-unit-1")


class CapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = CapabilityRegistry()
        self.registry.register(Capability(name="filesystem.read"))
        self.registry.register(Capability(name="filesystem.write"))

    def test_exact_match(self):
        self.assertEqual(self.registry.match("filesystem.read").status, MatchStatus.MATCH)

    def test_missing_capability_denies(self):
        self.assertEqual(self.registry.match("database.delete").status, MatchStatus.DENY)

    def test_wildcard_match(self):
        self.assertEqual(self.registry.match("filesystem.*").status, MatchStatus.MATCH)

    def test_unavailable_capability_denies_with_reason(self):
        self.registry.set_availability("filesystem.write", False)
        result = self.registry.match("filesystem.write")
        self.assertEqual(result.status, MatchStatus.DENY)
        self.assertIn("unavailable", result.reason)

    def test_scope_mismatch_denies(self):
        self.registry.register(Capability(name="database.delete", scopes=("admin",)))
        result = self.registry.match("database.delete", scopes=["readonly"])
        self.assertEqual(result.status, MatchStatus.DENY)


class PolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = PolicyEngine()
        self.policy.add_policy(
            PermissionPolicy(name="wildcard-deny", effect=Decision.DENY, action="*", resource="*")
        )

    def _req(self, action: str, resource: str, risk: float = 0.0) -> PermissionRequest:
        return PermissionRequest(
            actor=AGENT, action=action, resource=resource, risk_score=risk
        )

    def test_default_deny(self):
        decision = self.policy.decide(self._req("anything", "else"))
        self.assertEqual(decision.decision, Decision.DENY)

    def test_explicit_allow_beats_wildcard_deny(self):
        self.policy.add_policy(
            PermissionPolicy(
                name="allow-fs",
                effect=Decision.ALLOW,
                action="filesystem.*",
                resource="filesystem.*",
            )
        )
        decision = self.policy.decide(self._req("filesystem.write", "filesystem.write"))
        self.assertEqual(decision.decision, Decision.ALLOW)

    def test_deny_wins_at_equal_specificity(self):
        self.policy.add_policy(
            PermissionPolicy(name="allow-read", effect=Decision.ALLOW, action="filesystem.read", resource="*")
        )
        self.policy.add_policy(
            PermissionPolicy(name="deny-read", effect=Decision.DENY, action="filesystem.read", resource="*")
        )
        decision = self.policy.decide(self._req("filesystem.read", "*"))
        self.assertEqual(decision.decision, Decision.DENY)
        self.assertIn("deny-wins", decision.reasons[0])


class SafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.safety = SafetyEvaluator(review_uncovered_risk=0.5)

    def _eval(self, capability: str, risk: float) -> SafetyDecisionValue:
        return self.safety.evaluate(
            SafetyRequest(action_name="x", capability=capability, inputs={}, risk_score=risk)
        ).decision

    def test_low_risk_uncovered_allowed(self):
        self.assertEqual(self._eval("tools.noop", 0.1), SafetyDecisionValue.ALLOW)

    def test_high_risk_uncovered_reviewed(self):
        self.assertEqual(self._eval("db.delete", 0.7), SafetyDecisionValue.REVIEW)

    def test_forbidden_capability_denies(self):
        self.safety.add_policy(
            SafetyPolicy(name="no-delete", forbidden_capabilities=frozenset({"filesystem.delete"}))
        )
        self.assertEqual(self._eval("filesystem.delete", 0.1), SafetyDecisionValue.DENY)

    def test_risk_ceiling_via_covered_capability_denies(self):
        self.safety.add_policy(
            SafetyPolicy(
                name="low-risk-fs",
                covered_capabilities=frozenset({"filesystem.*"}),
                max_risk_score=0.3,
            )
        )
        self.assertEqual(self._eval("filesystem.write", 0.6), SafetyDecisionValue.DENY)


class ConstitutionTests(unittest.TestCase):
    def test_denies_forbidden_capability(self):
        constitution = AgentConstitution(
            principles=[
                Principle(
                    id="no-destructive",
                    statement="never use destructive capabilities",
                    category=PrincipleCategory.NO_HARM,
                    forbidden_capabilities=frozenset({"filesystem.delete"}),
                )
            ]
        )
        decision = constitution.check("rm", "filesystem.delete")
        self.assertEqual(decision.verdict, EnforcementVerdict.DENY)

    def test_review_required_for_reviewed_capability(self):
        constitution = AgentConstitution(
            principles=[
                Principle(
                    id="review-delete",
                    statement="require review for deletes",
                    review_capabilities=frozenset({"database.delete"}),
                )
            ]
        )
        decision = constitution.check("delete_row", "database.delete")
        self.assertEqual(decision.verdict, EnforcementVerdict.REVIEW)


if __name__ == "__main__":
    unittest.main()