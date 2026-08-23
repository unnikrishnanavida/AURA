from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from kernel.permissions import PermissionDecision, PermissionRule, Permissions


class PermissionsTestCase(unittest.TestCase):
    def test_unknown_request_is_denied_by_default(self) -> None:
        engine = Permissions()

        decision = engine.evaluate("alice", "read", "document:123")

        self.assertEqual(decision, PermissionDecision.DENY)

    def test_allow_rule_matches_subject_action_and_resource(self) -> None:
        engine = Permissions()
        engine.register_rule(
            PermissionRule(
                name="allow_docs_read",
                effect=PermissionDecision.ALLOW,
                subject_pattern="alice",
                action_pattern="read",
                resource_pattern="docs/*",
            )
        )

        decision = engine.evaluate("alice", "read", "docs/report.txt")

        self.assertEqual(decision, PermissionDecision.ALLOW)

    def test_higher_priority_deny_rule_wins(self) -> None:
        engine = Permissions()
        engine.register_rule(
            PermissionRule(
                name="allow_general",
                effect=PermissionDecision.ALLOW,
                subject_pattern="*",
                action_pattern="read",
                resource_pattern="*",
                priority=10,
            )
        )
        engine.register_rule(
            PermissionRule(
                name="deny_sensitive",
                effect=PermissionDecision.DENY,
                subject_pattern="alice",
                action_pattern="read",
                resource_pattern="docs/secret/*",
                priority=100,
            )
        )

        decision = engine.evaluate("alice", "read", "docs/secret/notes.txt")

        self.assertEqual(decision, PermissionDecision.DENY)

    def test_context_conditions_are_applied(self) -> None:
        engine = Permissions()
        engine.register_rule(
            PermissionRule(
                name="tenant_scoped_allow",
                effect=PermissionDecision.ALLOW,
                subject_pattern="alice",
                action_pattern="read",
                resource_pattern="docs/*",
                conditions={"tenant_id": "acme"},
            )
        )

        self.assertEqual(
            engine.evaluate("alice", "read", "docs/report.txt", context={"tenant_id": "acme"}),
            PermissionDecision.ALLOW,
        )
        self.assertEqual(
            engine.evaluate("alice", "read", "docs/report.txt", context={"tenant_id": "other"}),
            PermissionDecision.DENY,
        )


if __name__ == "__main__":
    unittest.main()
