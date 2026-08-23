"""Constitution checker: evaluates actions against constitutional principles.

The constitution is the highest-priority hard boundary in the runtime. A
``DENY`` here is absolute: autonomy, permissions, and safety reasoning may not
overturn it. REVIEW forces a human/controller approval gate regardless of
autonomy mode.
"""

from __future__ import annotations

from aura_agent.constitution.enforcement.enforcement_decision import (
    EnforcementDecision,
    EnforcementVerdict,
)
from aura_agent.constitution.principles.principle import Principle

__all__ = ["ConstitutionChecker"]


class ConstitutionChecker:
    """Validates actions against an ordered principle list."""

    def __init__(self, principles: list[Principle] | None = None) -> None:
        self._principles: list[Principle] = sorted(
            principles or [], key=lambda p: p.priority, reverse=True
        )

    def add_principle(self, principle: Principle) -> None:
        self._principles.append(principle)
        self._principles.sort(key=lambda p: p.priority, reverse=True)

    def principles(self) -> list[Principle]:
        return list(self._principles)

    def check(self, action: str, capability: str) -> EnforcementDecision:
        """Check an action+capability against every principle."""
        reasons: list[str] = []
        violations: list[str] = []
        review_needed = False

        for principle in self._principles:
            if principle.forbids_capability(capability):
                # deny wins immediately regardless of other principles
                return EnforcementDecision(
                    verdict=EnforcementVerdict.DENY,
                    reasons=[
                        f"principle {principle.id!r} forbids capability {capability!r}"
                    ],
                    violated_principles=[principle.id],
                )
            if principle.forbids_action(action):
                return EnforcementDecision(
                    verdict=EnforcementVerdict.DENY,
                    reasons=[
                        f"principle {principle.id!r} forbids action {action!r}"
                    ],
                    violated_principles=[principle.id],
                )
            if principle.reviews_capability(capability):
                review_needed = True
                reasons.append(
                    f"principle {principle.id!r} requires review for {capability!r}"
                )

        if review_needed:
            return EnforcementDecision(
                verdict=EnforcementVerdict.REVIEW,
                reasons=reasons,
                requires_approval=True,
            )
        return EnforcementDecision(
            verdict=EnforcementVerdict.ALLOW,
            reasons=[f"constitution permits {action!r} on {capability!r}"],
        )