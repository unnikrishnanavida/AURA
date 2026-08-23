"""Permission domain models."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field

from aura_agent.contracts.ids import AgentId

__all__ = ["PermissionRequest", "PermissionDecision", "Decision", "PermissionPolicy"]


class Decision(enum.Enum):
    """Authoritative permission outcome."""

    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class PermissionRequest:
    """What the actor is asking to do.

    Fields are explicit; authorization is never derived from truthiness of
    ad-hoc attributes.
    """

    actor: AgentId
    action: str
    resource: str
    scope: str = "*"
    operation: str = "execute"
    risk_score: float = 0.0
    context: dict = field(default_factory=dict)
    autonomy_mode: str | None = None


@dataclass(frozen=True)
class PermissionDecision:
    """An explainable authorization verdict."""

    request: PermissionRequest
    decision: Decision
    reasons: list[str]
    matched_policy: str | None = None
    requires_approval: bool = False

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


@dataclass(frozen=True)
class PermissionPolicy:
    """An explicit allow/deny rule over resources and scopes.

    ``action`` and ``resource`` support ``*`` wildcards; ``resource`` also
    supports trailing ``/*`` for prefix matching. Policies are declarative,
    not executable code.
    """

    name: str
    effect: Decision
    action: str = "*"
    resource: str = "*"
    scope: str = "*"
    min_risk_for_approval: float = float("inf")
    priority: int = 0

    def _matches_glob(self, value: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith("/*"):
            return value.startswith(pattern[:-1])
        return value == pattern or bool(re.fullmatch(pattern.replace("*", ".*"), value))

    def matches(self, request: PermissionRequest) -> bool:
        if not self._matches_glob(request.action, self.action):
            return False
        if not self._matches_glob(request.resource, self.resource):
            return False
        if self.scope != "*" and request.scope != self.scope:
            return False
        return True
