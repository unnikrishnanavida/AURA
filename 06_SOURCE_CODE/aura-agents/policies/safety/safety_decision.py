"""Safety decision models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime

__all__ = ["SafetyDecisionValue", "SafetyRequest", "SafetyDecision", "SafetyPolicy"]


class SafetyDecisionValue(enum.Enum):
    """Authoritative safety verdicts.

    - ``ALLOW``: safe to execute.
    - ``REVIEW``: cannot be confidently evaluated; needs a human or a stricter
      approval gate. Defaults toward REVIEW for unknown dangerous operations.
    - ``DENY``: a safety policy forbids it. Autonomy can never overturn this.
    """

    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(frozen=True)
class SafetyRequest:
    """What the safety engine evaluates."""

    action_name: str
    capability: str
    inputs: dict
    risk_score: float
    autonomy_mode: str | None = None


@dataclass(frozen=True)
class SafetyDecision:
    """An explainable safety verdict."""

    decision: SafetyDecisionValue
    risk_score: float
    reasons: list[str]
    violated_policies: list[str] = field(default_factory=list)
    required_approval: bool = False
    evaluated_action: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def allowed(self) -> bool:
        return self.decision is SafetyDecisionValue.ALLOW


@dataclass(frozen=True)
class SafetyPolicy:
    """An explicit safety rule.

    - ``forbidden_capabilities`` deny whole capability families (supports ``.*``).
    - ``review_capabilities`` force REVIEW (approval even in autonomous mode).
    - ``covered_capabilities`` declare this policy *evaluates* these
      capabilities and sets ``max_risk_score`` as the ceiling for them.
      Capabilities covered by no policy at all are treated as "unconfidently
      evaluated": medium+ risk becomes REVIEW rather than being silently
      denied or silently allowed.
    """

    name: str
    description: str = ""
    max_risk_score: float = float("inf")
    forbidden_capabilities: frozenset[str] = frozenset()
    review_capabilities: frozenset[str] = frozenset()
    covered_capabilities: frozenset[str] = frozenset()

    def _matches(self, capability: str, patterns: frozenset[str]) -> bool:
        for pattern in patterns:
            if pattern.endswith(".*"):
                if capability.startswith(pattern[:-2].rstrip(".") + "."):
                    return True
            elif pattern == capability:
                return True
        return False

    def applies_to(self, capability: str) -> bool:
        """True when this policy forbids, reviews, or covers ``capability``."""
        return (
            self._matches(capability, self.forbidden_capabilities)
            or self._matches(capability, self.review_capabilities)
            or self._matches(capability, self.covered_capabilities)
        )

    def covers_capability(self, capability: str) -> bool:
        """True when this policy explicitly evaluates ``capability``."""
        return self._matches(capability, self.covered_capabilities)

    def requires_review(self, capability: str) -> bool:
        return self._matches(capability, self.review_capabilities)

    def forbids_capability(self, capability: str) -> bool:
        return self._matches(capability, self.forbidden_capabilities)
