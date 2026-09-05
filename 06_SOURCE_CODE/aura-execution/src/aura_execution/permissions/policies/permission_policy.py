"""Permission policy: static policy decisions keyed by (principal, permission)."""

from __future__ import annotations


class PermissionPolicy:
    """Maps (principal, permission) -> "allow" | "deny" | "review".

    The policy defaults to explicit allow only: anything not granted is
    denied (fail closed).
    """

    def __init__(self, rules: dict[tuple[str, str], str] | None = None) -> None:
        self.rules = dict(rules or {})

    def grant(self, principal: str, permission: str, decision: str = "allow") -> None:
        self.rules[(principal, permission)] = decision

    def decide(self, principal: str, permission: str) -> str:
        return self.rules.get((principal, permission), "deny")

    def principal_granted(self, principal: str) -> bool:
        return any(k[0] == principal and v == "allow" for k, v in self.rules.items())


__all__ = ["PermissionPolicy"]