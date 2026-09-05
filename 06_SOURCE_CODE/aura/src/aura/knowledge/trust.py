"""Trust model.

Combines source reliability, evidence quality, verification status, and
freshness into a single trust-weighted confidence for a claim.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aura.knowledge.models import Claim, VerificationStatus


class TrustModel:
    """Computes the trust-weighted assessment of a claim."""

    freshness_half_life_days: float = 30.0

    def assess(self, claim: Claim, *, now: datetime | None = None) -> dict[str, float]:
        if not claim.evidence:
            return {"trust": 0.0, "evidence_support": 0.0, "source_reliability": 0.0, "freshness": 0.0}

        evidence_support = sum(e.quality for e in claim.evidence) / len(claim.evidence)
        source_reliability = sum(e.source.reliability for e in claim.evidence) / len(claim.evidence)
        freshness = self._freshness(claim, now or datetime.now(UTC))

        verification_multiplier = {
            VerificationStatus.UNVERIFIED: 0.5,
            VerificationStatus.VERIFIED: 1.0,
            VerificationStatus.REFUTED: 0.0,
            VerificationStatus.CONTESTED: 0.3,
        }[claim.status]

        trust = evidence_support * source_reliability * freshness * verification_multiplier
        return {
            "trust": round(min(1.0, trust), 6),
            "evidence_support": round(evidence_support, 6),
            "source_reliability": round(source_reliability, 6),
            "freshness": round(freshness, 6),
        }

    def _freshness(self, claim: Claim, now: datetime) -> float:
        created = claim.created_at
        if created is None:
            maybe = claim.provenance.details.get("created_at")
            created = maybe if isinstance(maybe, datetime) else None
        if created is None:
            return 0.5
        age_days = (now - created).total_seconds() / 86400.0
        if self.freshness_half_life_days <= 0:
            return 0.0
        return float(round(0.5 ** (age_days / self.freshness_half_life_days), 6))


__all__ = ["TrustModel"]