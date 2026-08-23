"""Goal conflict detection.

A conflict is a *provable contradiction* between goals' constraints or success
criteria over the same world-state field. Detection is deterministic and
evidence-based -- it never guesses.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_agent.goals.models.goal import Goal, GoalId

__all__ = ["GoalConflict", "ConflictDetector"]


@dataclass(frozen=True)
class GoalConflict:
    """A detected conflict between two goals."""

    left: GoalId
    right: GoalId
    field: str
    reason: str


class ConflictDetector:
    """Detects pairwise goal conflicts over the constraint model."""

    def detect(self, goals: list[Goal]) -> list[GoalConflict]:
        """Return all pairwise conflicts among ``goals``."""
        conflicts: list[GoalConflict] = []
        for i in range(len(goals)):
            for j in range(i + 1, len(goals)):
                a, b = goals[i], goals[j]
                for ca in a.constraints:
                    for cb in b.constraints:
                        if ca.field != cb.field:
                            continue
                        intersection = ca.allowed & cb.allowed
                        if not intersection and ca.allowed and cb.allowed:
                            conflicts.append(
                                GoalConflict(
                                    left=a.id,
                                    right=b.id,
                                    field=ca.field,
                                    reason=(
                                        f"goals constrain {ca.field!r} to disjoint "
                                        f"value sets {sorted(ca.allowed)} vs {sorted(cb.allowed)}"
                                    ),
                                )
                            )
        return conflicts
