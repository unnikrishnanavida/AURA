"""Unit tests for freshness / temporal knowledge in aura-knowledge.

Freshness is represented explicitly: stale evidence degrades a claim to
OUTDATED and blocks verification. Fresh evidence restores it.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import (
    ClaimStatus,
    Evidence,
    FreshnessEngine,
    KnowledgeEngine,
    Source,
    VerificationStatus,
)


def _src(rep=0.8):
    return Source(identifier="s", reputation=rep)


def _old_evidence():
    return Evidence(
        content="old",
        support=1.0,
        reliability=0.9,
        source=_src(),
        captured_at=datetime.now(timezone.utc) - timedelta(days=30),
    )


def test_stale_knowledge_becomes_outdated():
    eng = KnowledgeEngine(freshness_ttl=timedelta(seconds=1))
    c = eng.add_claim("stale claim")
    eng.add_evidence(c.claim_id, _old_evidence())
    eng.verify(c.claim_id)
    assert c.status is ClaimStatus.OUTDATED
    assert c.verification is VerificationStatus.UNVERIFIED


def test_fresh_evidence_restores_claim():
    eng = KnowledgeEngine(freshness_ttl=timedelta(days=365))
    c = eng.add_claim("fresh claim")
    eng.add_evidence(
        c.claim_id,
        Evidence(
            content="fresh",
            support=1.0,
            reliability=0.9,
            source=_src(),
            captured_at=datetime.now(timezone.utc),
        ),
    )
    eng.verify(c.claim_id)
    assert c.status is ClaimStatus.SUPPORTED
    assert c.verification is VerificationStatus.VERIFIED


def test_freshness_engine_decay():
    engine = FreshnessEngine(ttl=timedelta(days=30))
    c = type("C", (), {"evidence": [_old_evidence()], "created_at": None, "status": None})()
    assert engine.is_fresh(c) is False


def test_freshness_half_life_decays_over_time():
    eng = KnowledgeEngine()
    now = datetime.now(timezone.utc)
    c = eng.add_claim("aging claim")
    eng.add_evidence(c.claim_id, Evidence(content="recent", support=1.0, reliability=0.9, source=_src(), captured_at=now))
    fresh_trust = eng.trust.assess(c, now=now)["freshness"]
    aged_trust = eng.trust.assess(c, now=now + timedelta(days=60))["freshness"]
    assert aged_trust < fresh_trust