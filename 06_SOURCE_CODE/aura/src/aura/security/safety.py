"""Safety evaluation.

Safety decisions are ALLOW, REVIEW, or DENY. Every decision is explainable.
Uncovered operations above a risk threshold default to REVIEW (a human gate),
never to silent allow or silent deny without explanation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from aura.foundation.errors import SafetyDeniedError
from aura.security.capabilities import name_matches


class SafetyDecision(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(frozen=True)
class SafetyResult:
    decision: SafetyDecision
    reason: str
    risk: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {"decision": self.decision.value, "reason": self.reason, "risk": self.risk}


@dataclass
class SafetyPolicy:
    """Configures allowed/reviewable/forbidden capabilities."""

    forbidden_capabilities: set[str] = field(default_factory=set)
    review_capabilities: set[str] = field(default_factory=set)
    covered_capabilities: set[str] = field(default_factory=set)
    max_allowed_risk: float = 0.5


class SafetyEvaluator:
    def __init__(self, policy: SafetyPolicy | None = None, review_uncovered_risk: float = 0.3) -> None:
        self._policy = policy or SafetyPolicy()
        self._review_uncovered_risk = review_uncovered_risk

    def evaluate(self, *, action: str, risk: float = 0.0) -> SafetyResult:
        if any(name_matches(forbidden, action) for forbidden in self._policy.forbidden_capabilities):
            return SafetyResult(SafetyDecision.DENY, f"action {action!r} is forbidden by safety policy", risk)
        covered = any(name_matches(pattern, action) for pattern in self._policy.covered_capabilities)
        if risk > self._policy.max_allowed_risk:
            return SafetyResult(SafetyDecision.DENY, f"risk {risk:.2f} exceeds allowed ceiling", risk)
        if any(name_matches(pattern, action) for pattern in self._policy.review_capabilities):
            return SafetyResult(SafetyDecision.REVIEW, f"action {action!r} requires safety review", risk)
        if not covered and risk > self._review_uncovered_risk:
            return SafetyResult(
                SafetyDecision.REVIEW, f"uncovered action {action!r} above review threshold", risk
            )
        return SafetyResult(SafetyDecision.ALLOW, f"action {action!r} is safe", risk)

    def enforce(self, *, action: str, risk: float = 0.0) -> SafetyResult:
        result = self.evaluate(action=action, risk=risk)
        if result.decision is SafetyDecision.DENY:
            raise SafetyDeniedError(result.reason)
        return result


__all__ = ["SafetyDecision", "SafetyEvaluator", "SafetyPolicy", "SafetyResult"]