"""Policy engine: deterministic, explainable authorization.

The engine evaluates a ``PermissionRequest`` against an explicit policy set.
Matching rules, applied deterministically:

1. The most specific matching policy wins (fewest ``*`` wildcards).
2. Among equally specific matches, ``DENY`` outranks ``ALLOW`` (deny-wins),
   then higher ``priority``.
3. If nothing matches, the decision is ``DENY`` (default-deny). New
   operations are never silently permitted.
"""

from __future__ import annotations

from aura_agent.contracts.errors import PermissionDenied
from aura_agent.policies.models import (
    Decision,
    PermissionDecision,
    PermissionPolicy,
    PermissionRequest,
)

__all__ = ["PolicyEngine"]


class PolicyEngine:
    """The single authoritative permission resolver."""

    def __init__(self) -> None:
        self._policies: list[PermissionPolicy] = []

    def add_policy(self, policy: PermissionPolicy) -> None:
        self._policies.append(policy)

    def policies(self) -> list[PermissionPolicy]:
        return list(self._policies)

    @staticmethod
    def _specificity_score(p: PermissionPolicy) -> int:
        """A policy is more specific when it has *more literal characters* in
        its action and resource patterns (fewer ``*`` wildcards). The
        explicit deny/allow patterns outrank the wildcard base rules."""
        literal_action = len(p.action.replace("*", ""))
        literal_resource = len(p.resource.replace("*", ""))
        return literal_action + literal_resource

    def _rank(self, p: PermissionPolicy) -> tuple[int, int, int]:
        """Rank a policy: specificity, then deny-first, then priority.

        Higher rank wins via ``max()``: more specific, then DENY over ALLOW,
        then higher priority.
        """
        deny_score = 1 if p.effect is Decision.DENY else 0
        return (self._specificity_score(p), deny_score, p.priority)

    def decide(self, request: PermissionRequest) -> PermissionDecision:
        """Evaluate the request and return the verdict without raising."""
        matching = [p for p in self._policies if p.matches(request)]
        if not matching:
            return PermissionDecision(
                request=request,
                decision=Decision.DENY,
                reasons=[
                    f"no policy matched action={request.action!r} "
                    f"resource={request.resource!r} (default-deny)"
                ],
            )

        chosen = max(matching, key=self._rank)

        if chosen.effect is Decision.DENY:
            return PermissionDecision(
                request=request,
                decision=Decision.DENY,
                reasons=[
                    f"denied by policy {chosen.name!r} "
                    "(most specific / deny-wins)"
                ],
                matched_policy=chosen.name,
            )

        if request.risk_score >= chosen.min_risk_for_approval:
            return PermissionDecision(
                request=request,
                decision=Decision.APPROVAL_REQUIRED,
                reasons=[
                    f"policy {chosen.name!r} allows but risk "
                    f"{request.risk_score:g} >= approval threshold "
                    f"{chosen.min_risk_for_approval:g}"
                ],
                matched_policy=chosen.name,
                requires_approval=True,
            )
        return PermissionDecision(
            request=request,
            decision=Decision.ALLOW,
            reasons=[f"allowed by policy {chosen.name!r}"],
            matched_policy=chosen.name,
        )

    def enforce(self, request: PermissionRequest) -> PermissionDecision:
        """Evaluate and raise :class:`PermissionDenied` when denied.

        ``APPROVAL_REQUIRED`` is *not* an error -- escalation is handled by
        the autonomy layer.
        """
        decision = self.decide(request)
        if decision.decision is Decision.DENY:
            raise PermissionDenied(
                f"permission denied: {'; '.join(decision.reasons)}"
            )
        return decision