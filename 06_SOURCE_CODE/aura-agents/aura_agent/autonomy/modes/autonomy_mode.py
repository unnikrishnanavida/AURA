"""Autonomy modes.

Autonomy determines *how much* an agent may decide without human/controller
approval. It is structured as an ordered scale; each mode raises or lowers the
approval threshold but never grants the authority to bypass constitution,
permission, capability, or safety denials.
"""

from __future__ import annotations

import enum

__all__ = ["AutonomyMode"]


class AutonomyMode(enum.IntEnum):
    """Ordered autonomy levels. ``MANUAL`` is the least autonomous.

    - ``MANUAL``: every action requires explicit approval.
    - ``ASSISTED``: routine low-risk actions proceed; everything else asks.
    - ``SUPERVISED``: actions up to medium risk proceed; high-risk asks.
    - ``AUTONOMOUS``: proceeds unless a hard boundary (safety / permission /
      constitution / budget) denies. Never bypasses those boundaries.
    """

    MANUAL = 0
    ASSISTED = 1
    SUPERVISED = 2
    AUTONOMOUS = 3

    def allows(self, *, risk_score: float) -> bool:
        """Whether an action at ``risk_score`` may proceed without approval
        under this mode.

        Ordering by the enum is authoritative; the thresholds are explicit so
        the mapping is deterministic and testable.
        """
        thresholds = {
            AutonomyMode.MANUAL: float("-inf"),  # never allows -> always asks
            AutonomyMode.ASSISTED: 0.35,
            AutonomyMode.SUPERVISED: 0.6,
            AutonomyMode.AUTONOMOUS: 0.85,
        }
        return risk_score < thresholds[self]

    @staticmethod
    def human_required_threshold() -> float:
        """Risk above which even autonomous operation must ask."""
        return 0.85