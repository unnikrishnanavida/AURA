"""Constitutional principles.

Principles are immutable, explicit rules an agent is never authorized to
violate, even in fully autonomous mode. They govern *capabilities* and
*action/resource patterns* rather than ad-hoc runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Principle", "PrincipleCategory"]


class PrincipleCategory:
    """Well-known constitutional categories."""

    NO_HARM = "no_harm"
    TRANSPARENCY = "transparency"
    HUMAN_DIRECTION = "human_direction"
    DATA_PRIVACY = "data_privacy"
    RESOURCE_LIMITS = "resource_limits"


@dataclass(frozen=True)
class Principle:
    """A single constitutional rule.

    ``forbidden_capabilities`` denies capability families (supports ``.*``),
    ``review_capabilities`` forces human/controller review, and
    ``forbidden_action_prefixes`` denies action name prefixes.
    """

    id: str
    statement: str
    category: str = PrincipleCategory.NO_HARM
    priority: int = 0  # higher runs first
    forbidden_capabilities: frozenset[str] = frozenset()
    review_capabilities: frozenset[str] = frozenset()
    forbidden_action_prefixes: frozenset[str] = frozenset()

    def forbids_capability(self, capability: str) -> bool:
        return any(_cap_matches(capability, c) for c in self.forbidden_capabilities)

    def reviews_capability(self, capability: str) -> bool:
        return any(_cap_matches(capability, c) for c in self.review_capabilities)

    def forbids_action(self, action: str) -> bool:
        return any(action.startswith(prefix.partition("*")[0]) for prefix in self.forbidden_action_prefixes)


def _cap_matches(capability: str, pattern: str) -> bool:
    if pattern.endswith(".*"):
        return capability.startswith(pattern[:-2].rstrip(".") + ".")
    return capability == pattern
