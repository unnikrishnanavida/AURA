"""Evidence fusion for aura-knowledge.

Fusion combines multiple pieces of evidence into a single confidence value
plus an explicit uncertainty. Conflicting evidence raises uncertainty rather
than being averaged away, because the conflict itself is informative.
"""

from __future__ import annotations

from collections.abc import Iterable

from aura_knowledge.core.models import Confidence, Evidence


class EvidenceFusion:
    """Fuse evidence into a confidence/uncertainty pair."""

    def fuse(self, evidence: Iterable[Evidence], *, base_uncertainty: float = 0.2) -> Confidence:
        """Fuse a set of evidence into :class:`Confidence`.

        - No evidence -> zero confidence, full uncertainty.
        - All evidence agrees -> confidence near the weighted average.
        - Conflicting evidence -> confidence moves toward zero and
          uncertainty rises proportional to the conflict.
        """
        evidence = list(evidence)
        if not evidence:
            return Confidence(value=0.0, uncertainty=1.0)

        weighted = sum(e.support * e.reliability * e.source.reputation for e in evidence)
        total_weight = sum(e.reliability * e.source.reputation for e in evidence)
        if total_weight == 0:
            return Confidence(value=0.0, uncertainty=1.0)

        raw = weighted / total_weight  # in [-1, 1]
        value = max(0.0, min(1.0, (raw + 1.0) / 2.0))

        # Scale confidence by source reputation: evidence from a
        # low-reputation source must not produce near-certain confidence.
        avg_reputation = sum(e.source.reputation for e in evidence) / len(evidence)
        value = value * (0.5 + 0.5 * avg_reputation)

        supports = [e for e in evidence if e.support > 0]
        contradicts = [e for e in evidence if e.support < 0]
        if supports and contradicts:
            # Explicit conflict: raise uncertainty, do not silently average.
            conflict = min(len(supports), len(contradicts)) / len(evidence)
            uncertainty = max(base_uncertainty, 0.5 + conflict * 0.4)
        else:
            # Agreement: uncertainty from evidence paucity and intrinsic noise.
            agreement = len(evidence) / (len(evidence) + 1.0)
            noise = 1.0 - min(e.reliability for e in evidence)
            uncertainty = max(base_uncertainty, (1.0 - agreement) * 0.4 + noise * 0.3)

        return Confidence(value=round(min(1.0, value), 6), uncertainty=round(min(1.0, uncertainty), 6))


__all__ = ["EvidenceFusion"]