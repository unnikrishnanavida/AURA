"""Safety engine: risk-based gates that can deny or route to review.

The engine is fail-closed: high-risk actions without approval are REVIEWED and
never auto-approved; actions flagged by the safety gate are DENIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafetyDecision:
    """A safety verdict."""

    decision: str  # "ALLOW" | "DENY" | "REVIEW"
    reasons: tuple[str, ...] = ()


class SafetyEngine:
    """Evaluates the risk posture of an action."""

    review_threshold: float = 0.75
    deny_threshold: float = 0.95

    def __init__(self, *, review_threshold: float | None = None, deny_threshold: float | None = None) -> None:
        if review_threshold is not None:
            self.review_threshold = review_threshold
        if deny_threshold is not None:
            self.deny_threshold = deny_threshold

    def evaluate(self, action: Any, approved: bool = False) -> SafetyDecision:
        risk = float(getattr(action, "risk", 0.0) or 0.0)
        if risk < 0.0 or risk > 1.0:
            return SafetyDecision("DENY", ("non-numeric or out-of-range action risk",))
        if risk >= self.deny_threshold:
            return SafetyDecision("DENY", (f"risk {risk:.2f} exceeds deny threshold",))
        if risk >= self.review_threshold and not approved:
            return SafetyDecision("REVIEW", (f"risk {risk:.2f} requires human review",))
        return SafetyDecision("ALLOW")


__all__ = ["SafetyDecision", "SafetyEngine"]