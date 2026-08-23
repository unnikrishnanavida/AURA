"""Learning bridge: converts validated reflection signals into genome updates.

The bridge enforces the learning boundary:

- only signals marked as validated by an explicit authorization may update
  learned behavior,
- signals that touch safety/permission/constitution domains are REFUSED at
  the bridge by default,
- every genome update is attributable (authorized_by + evidence).

The bridge talks to the genome through its public model contract, never to
internal runtime values.
"""

from __future__ import annotations

from aura_agent.contracts.ids import AgentId
from aura_agent.genome.agent_genome import AgentGenome, GenomeUpdate
from aura_agent.reflection.models import ImprovementSignal

__all__ = ["LearningBridge", "LearningVerdict"]


class LearningVerdict:
    """Enum-like constants for the learning gate."""

    APPLIED = "applied"
    REFUSED_SAFETY_RELEVANT = "refused_safety_relevant"
    REFUSED_UNVALIDATED = "refused_unvalidated"
    IGNORED_NO_TARGET = "ignored_no_target"


class LearningBridge:
    """Filters signals and applies only validated ones to the genome."""

    def __init__(
        self,
        genome: AgentGenome,
        *,
        authorize_safety_relevant: bool = False,
    ) -> None:
        self._genome = genome
        self._authorize_safety = authorize_safety_relevant

    def ingest(
        self,
        signal: ImprovementSignal,
        *,
        authorized_by: str | None = None,
    ) -> str:
        """Attempt to apply a reflection signal to the genome.

        Returns a ``LearningVerdict`` string explaining the outcome.
        """
        if signal.is_safety_relevant() and not self._authorize_safety:
            return LearningVerdict.REFUSED_SAFETY_RELEVANT

        if not signal.signal_type.startswith("strategy.") and not signal.signal_type.startswith("efficiency."):
            return LearningVerdict.REFUSED_UNVALIDATED

        if authorized_by is None:
            return LearningVerdict.REFUSED_UNVALIDATED

        if not signal.target:
            return LearningVerdict.IGNORED_NO_TARGET

        self._genome.apply_learned_update(
            GenomeUpdate(
                authorized_by=authorized_by,
                evidence={
                    "signal_type": signal.signal_type,
                    "suggestion": signal.suggestion,
                    "evidence": signal.evidence,
                },
            ),
            behavior_key=f"{signal.signal_type}:{signal.target}",
            value=signal.suggestion,
        )
        return LearningVerdict.APPLIED