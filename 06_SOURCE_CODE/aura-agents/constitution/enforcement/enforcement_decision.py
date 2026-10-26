"""Constitution enforcement decision."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

__all__ = ["EnforcementVerdict", "EnforcementDecision"]


class EnforcementVerdict(enum.Enum):
    """Constitutional verdict for an action."""

    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(frozen=True)
class EnforcementDecision:
    """Result of checking an action against the constitution."""

    verdict: EnforcementVerdict
    reasons: list[str]
    violated_principles: list[str] = field(default_factory=list)
    requires_approval: bool = False

    @property
    def allowed(self) -> bool:
        return self.verdict is EnforcementVerdict.ALLOW
