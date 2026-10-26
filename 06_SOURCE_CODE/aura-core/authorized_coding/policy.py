"""Action policy: risk, approval requirements, and role gates.

The policy is the single authority for "who may perform which action" and
"which actions need approval". It composes with the execution engine -- an
action that the policy says ``requires_approval`` is never executed; the
engine turns it into an approval record instead. Unknown actions are denied.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .models import ActionName, InputSpec

__all__ = [
    "RiskLevel",
    "PolicyDecision",
    "ActionPolicyEntry",
    "ActionPolicy",
    "default_policy",
    "register_default_actions",
]


class RiskLevel(int, Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REQUIRES_APPROVAL = "requires_approval"
    DENY = "deny"


@dataclass(frozen=True)
class ActionPolicyEntry:
    name: ActionName
    risk: RiskLevel
    requires_approval: bool
    allowed_roles: tuple[str, ...] = ("agent", "admin")
    description: str = ""
    input_spec: InputSpec = field(default_factory=InputSpec)


class ActionPolicy:
    """Owns per-action policy decisions with fail-closed defaults."""

    def __init__(self) -> None:
        self._entries: dict[ActionName, ActionPolicyEntry] = {}

    def register(self, entry: ActionPolicyEntry) -> None:
        self._entries[entry.name] = entry

    def evaluate(
        self,
        action: ActionName,
        actor: str,
        *,
        roles: Iterable[str] | None = None,
    ) -> tuple[PolicyDecision, str]:
        """Return ``(decision, reason)``. Fail-closed: unknown actions and
        actions whose roles are not granted are denied."""
        entry = self._entries.get(action)
        if entry is None:
            return PolicyDecision.DENY, f"action not registered: {action!r}"
        allowed = set(entry.allowed_roles) if roles is None else set(roles)
        if entry.allowed_roles and not (allowed & set(entry.allowed_roles)):
            return PolicyDecision.DENY, (
                f"actor {actor!r} lacks {entry.allowed_roles!r} for {action!r}"
            )
        if entry.requires_approval:
            return PolicyDecision.REQUIRES_APPROVAL, (
                f"action {action!r} is approval-gated (risk {entry.risk.name})"
            )
        return PolicyDecision.ALLOW, f"action {action!r} is allowed (risk {entry.risk.name})"

    def diagnose(self) -> dict[str, dict[str, object]]:
        """Machine-readable policy table for tooling and dashboards."""
        out: dict[str, dict[str, object]] = {}
        for name, entry in sorted(self._entries.items()):
            out[name.value] = {
                "risk": entry.risk.name,
                "requires_approval": entry.requires_approval,
                "allowed_roles": list(entry.allowed_roles),
            }
        return out

    def action_spec(self, action: ActionName) -> InputSpec | None:
        """Input schema for a single action, or None when unset."""
        entry = self._entries.get(action)
        if entry is None:
            return None
        fields: list[InputField] = []
        for spec in getattr(entry, "input_spec", None) or []:
            fields.append(spec)
        return InputSpec(tuple(fields))


def default_policy() -> ActionPolicy:
    """The smallest complete policy surface for project actions."""
    policy = ActionPolicy()
    policy.register(
        ActionPolicyEntry(
            name=ActionName.LIST_FILES,
            risk=RiskLevel.LOW,
            requires_approval=False,
            allowed_roles=("agent", "admin", "viewer"),
            description="list files in the workspace",
        )
    )
    policy.register(
        ActionName.READ_FILE,
        risk=RiskLevel.LOW,
        requires_approval=False,
        allowed_roles=("agent", "admin", "viewer"),
        description="read a text file in the workspace",
    )
    policy.register(
        ActionName.WRITE_TEXT,
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
        allowed_roles=("agent", "admin"),
        description="write or overwrite a text file (needs approval)",
    )
    policy.register(
        ActionName.PATCH_FILE,
        risk=RiskLevel.HIGH,
        requires_approval=True,
        allowed_roles=("agent", "admin"),
        description="apply a unified diff to a text file (needs approval)",
    )
    policy.register(
        ActionName.DELETE_FILE,
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
        allowed_roles=("agent", "admin"),
        description="delete a file or directory (needs approval)",
    )
    policy.register(
        ActionName.CREATE_DIRECTORY,
        risk=RiskLevel.LOW,
        requires_approval=False,
        allowed_roles=("agent", "admin"),
        description="create a directory in the workspace",
    )
    return policy
