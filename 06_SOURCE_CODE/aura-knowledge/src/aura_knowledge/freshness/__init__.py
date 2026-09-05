"""Freshness and temporal knowledge for aura-knowledge.

Freshness is represented explicitly: every evidence item carries a capture
time, and claims decay to :class:`ClaimStatus.OUTDATED` when their evidence is
older than the configured TTL. An outdated claim cannot verify until fresh
evidence arrives.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aura_knowledge.core.models import Claim, ClaimStatus


class FreshnessEngine:
    """Evaluates and enforces knowledge freshness."""

    def __init__(self, ttl: timedelta | None = None, *, now: datetime | None = None) -> None:
        self.ttl = ttl or timedelta(days=30)
        self._now = now

    def is_fresh(self, claim: Claim) -> bool:
        reference = self._latest_capture(claim)
        if reference is None:
            return True  # no temporal claim to go stale
        now = self._now or datetime.now(UTC)
        return (now - reference) <= self.ttl

    def apply_freshness(self, claim: Claim) -> Claim:
        """Set status to OUTDATED when evidence is stale.

        Restores a previously OUTDATED claim to UNVERIFIED when fresh evidence
        arrives, so it can be re-evaluated and verified again.
        """
        if not claim.evidence:
            return claim
        if self.is_fresh(claim):
            if claim.status is ClaimStatus.OUTDATED:
                claim.status = ClaimStatus.UNVERIFIED
            return claim
        claim.status = ClaimStatus.OUTDATED
        claim.verification = type(claim.verification).UNVERIFIED
        return claim

    def _latest_capture(self, claim: Claim) -> datetime | None:
        captured = [e.captured_at for e in claim.evidence if e.captured_at is not None]
        if not captured:
            return claim.created_at
        return max(captured)


__all__ = ["FreshnessEngine"]