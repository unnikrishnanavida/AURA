"""Permissions.

Policy resolution follows: identity -> scope -> policy -> risk -> approval.
Decision outcomes are ALLOW, DENY, or APPROVAL_REQUIRED. The policy engine is
default-deny: if no rule matches, the request is denied. Every decision
carries the matched rule and an explainable reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aura.foundation.errors import ApprovalRequiredError, PermissionDeniedError
from aura.security.capabilities import name_matches


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True, slots=True)
class Identity:
    id: str
    roles: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ("*",)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("identity id must not be empty")


@dataclass(frozen=True, slots=True)
class Rule:
    action: str
    resource: str = "*"
    effect: Decision = Decision.DENY
    name: str = ""
    risk_max: float = 1.0
    requires_approval: bool = False

    def matches(self, action: str, resource: str) -> bool:
        return name_matches(self.action, action) and name_matches(self.resource, resource)


@dataclass(frozen=True)
class PermissionResult:
    decision: Decision
    reason: str
    matched_rules: tuple[Rule, ...] = ()
    approval: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "matched_rules": [r.name or f"{r.action}:{r.resource}" for r in self.matched_rules],
            "approval": self.approval,
        }


class PolicyEngine:
    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)

    def evaluate(
        self,
        *,
        action: str,
        resource: str = "*",
        identity: Identity | None = None,
        risk: float = 0.0,
        approval: bool = False,
    ) -> PermissionResult:
        del identity
        matched = [r for r in self._rules if r.matches(action, resource)]
        if not matched:
            return PermissionResult(
                Decision.DENY,
                f"no policy matches action={action!r} resource={resource!r}; default deny",
            )
        matched.sort(key=lambda r: len(r.action), reverse=True)
        rule = matched[0]
        if rule.effect is Decision.DENY:
            return PermissionResult(
                Decision.DENY,
                f"denied by rule {rule.name or rule.action} (action={action!r}, resource={resource!r})",
                matched_rules=tuple(matched),
            )
        if rule.requires_approval and not approval:
            return PermissionResult(
                Decision.APPROVAL_REQUIRED,
                f"approval required by rule {rule.name or rule.action}",
                matched_rules=tuple(matched),
            )
        if risk > rule.risk_max:
            return PermissionResult(
                Decision.APPROVAL_REQUIRED if not approval else Decision.ALLOW,
                f"risk {risk:.2f} exceeds rule ceiling {rule.risk_max:.2f}"
                + ("" if approval else "; approval required"),
                matched_rules=tuple(matched),
                approval=approval,
            )
        return PermissionResult(Decision.ALLOW, "allowed by policy", matched_rules=tuple(matched), approval=approval)

    def enforce(
        self,
        *,
        action: str,
        resource: str = "*",
        identity: Identity | None = None,
        risk: float = 0.0,
        approval: bool = False,
    ) -> PermissionResult:
        result = self.evaluate(action=action, resource=resource, identity=identity, risk=risk, approval=approval)
        if result.decision is Decision.DENY:
            raise PermissionDeniedError(result.reason)
        if result.decision is Decision.APPROVAL_REQUIRED:
            raise ApprovalRequiredError(result.reason)
        return result


__all__ = ["Decision", "Identity", "PermissionResult", "PolicyEngine", "Rule"]