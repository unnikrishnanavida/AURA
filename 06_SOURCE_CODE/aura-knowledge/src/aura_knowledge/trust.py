"""Trust scoring for aura-knowledge.

Trust is a composite of source reputation, evidence reliability/quality,
freshness, and verification state. Trust is NOT confidence: confidence is a
property of the belief in the proposition, while trust reflects how much the
body of evidence and provenance deserves belief.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aura_knowledge.core.models import Claim, VerificationStatus


class TrustModel:
    """Computes the trust-weighted assessment of a claim."""

    freshness_half_life_days: float = 30.0

    def assess(self, claim: Claim, *, now: datetime | None = None) -> dict[str, float]:
        """Return a trust breakdown for the claim.

        A claim with no evidence receives zero trust: evidence is required
        before anything can be believed enough to be knowledge.
        """
        now = now or datetime.now(UTC)
        if not claim.evidence:
            return {
                "trust": 0.0,
                "evidence_quality": 0.0,
                "source_reputation": 0.0,
                "freshness": 0.0,
                "verification_multiplier": 0.5,
            }

        evidence_quality = sum(e.reliability * (1.0 - abs(e.support)) * 0.1 + e.reliability for e in claim.evidence) / len(claim.evidence)
        source_reputation = sum(e.source.reputation for e in claim.evidence) / len(claim.evidence)
        freshness = self.freshness(claim, now)

        multiplier = {
            VerificationStatus.UNVERIFIED: 0.5,
            VerificationStatus.VERIFIED: 1.0,
            VerificationStatus.REFUTED: 0.0,
            VerificationStatus.CONTESTED: 0.3,
        }[claim.verification]

        trust = evidence_quality * source_reputation * freshness * multiplier
        return {
            "trust": round(min(1.0, trust), 6),
            "evidence_quality": round(evidence_quality, 6),
            "source_reputation": round(source_reputation, 6),
            "freshness": round(freshness, 6),
            "verification_multiplier": multiplier,
        }

    def freshness(self, claim: Claim, now: datetime) -> float:
        """Freshness decays with the age of the most recent evidence."""
        if not claim.evidence:
            return 0.5
        captured = [e.captured_at for e in claim.evidence if e.captured_at is not None]
        if not captured:
            # fall back to claim creation time
            if claim.created_at is None:
                return 0.5
            reference = claim.created_at
        else:
            reference = max(captured)
        age_days = (now - reference).total_seconds() / 86400.0
        if self.freshness_half_life_days <= 0:
            return 0.0
        return float(round(0.5 ** (age_days / self.freshness_half_life_days), 6))


__all__ = ["TrustModel"]