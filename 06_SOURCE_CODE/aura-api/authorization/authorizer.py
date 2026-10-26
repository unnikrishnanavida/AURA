"""Authorization for aura-api (RBAC + ABAC).

Authorization MUST fail closed: any lookup or policy evaluation that cannot
prove access is granted must deny. There is no default-allow path.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aura_api.core.context import Principal
from aura_api.core.errors import AuthorizationError

Policy = Callable[[Principal, str, dict[str, Any]], bool]


@dataclass(frozen=True)
class RoleBinding:
    """A role attached to a resource."""

    role: str
    resource_type: str
    action: str


@dataclass
class RBACPolicy:
    """Role-based access control over (resource_type, action)."""

    allowed: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    def grant(self, *, role: str, resource_type: str, action: str) -> None:
        self.allowed.setdefault((resource_type, action), set()).add(role)

    def check(self, principal: Principal, resource_type: str, action: str) -> bool:
        """Fail-closed: unknown roles/actions are denied."""
        expected = self.allowed.get((resource_type, action), set())
        return any(role in expected for role in principal.roles)


@dataclass(frozen=True)
class AbacRule:
    """An attribute-based rule evaluated against principal attributes."""

    resource_type: str
    action: str
    predicate: Callable[[dict[str, Any]], bool]
    description: str = ""


@dataclass
class ABACPolicy:
    """Attribute-based access control over (resource_type, action)."""

    rules: list[AbacRule] = field(default_factory=list)

    def add_rule(self, resource_type: str, action: str, predicate: Callable[[dict[str, Any]], bool], *, description: str = "") -> None:
        self.rules.append(AbacRule(resource_type=resource_type, action=action, predicate=predicate, description=description))

    def check(self, principal: Principal, resource_type: str, action: str) -> bool:
        for rule in self.rules:
            if (rule.resource_type, rule.action) == (resource_type, action) and rule.predicate(dict(principal.attributes)):
                return True
        return False  # fail closed


class Authorizer:
    """Composes RBAC + ABAC with fail-closed semantics."""

    def __init__(self, rbac: RBACPolicy | None = None, abac: ABACPolicy | None = None) -> None:
        self.rbac = rbac or RBACPolicy()
        self.abac = abac or ABACPolicy()

    def is_allowed(self, principal: Principal, resource_type: str, action: str) -> bool:
        return self.rbac.check(principal, resource_type, action) or self.abac.check(principal, resource_type, action)

    def authorize(self, principal: Principal, resource_type: str, action: str) -> None:
        """Fail-closed gate: raises AuthorizationError unless access is proven."""
        if principal is None or not principal.is_authenticated:
            raise AuthorizationError("anonymous calls are not authorized")
        if not self.is_allowed(principal, resource_type, action):
            raise AuthorizationError(f"principal {principal.subject!r} is not allowed to {action} {resource_type}")


__all__ = ["ABACPolicy", "AbacRule", "Authorizer", "RBACPolicy", "RoleBinding"]