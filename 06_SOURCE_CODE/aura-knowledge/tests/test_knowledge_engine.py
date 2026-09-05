"""Behavioral tests for the AURA Knowledge engine."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aura_knowledge import KnowledgeEngine
from aura_knowledge.core.models import ClaimStatus, Confidence, Evidence, Source, VerificationStatus


def _src(kind="experiment", rep=0.8):
    return Source(identifier=f"src-{kind}-{rep}", kind=kind, reputation=rep)


def _ev(content, support, reliability=0.9, src=None):
    return Evidence(content=content, support=support, reliability=reliability, source=src or _src())


def test_unsupported_claim_never_verified():
    eng = KnowledgeEngine()
    c = eng.add_claim("the sky is green")
    eng.verify(c.claim_id)
    assert c.status is ClaimStatus.UNSUPPORTED
    assert c.verification is VerificationStatus.UNVERIFIED


def test_confidence_and_verification_are_distinct():
    # Strong but UNVERIFIED -> not actionable as fact
    eng = KnowledgeEngine()
    c = eng.add_claim("claim with strong support but no verification")
    eng.add_evidence(c.claim_id, _ev("supports strongly", 1.0))
    assert c.confidence.value >= 0.9
    assert c.verification is VerificationStatus.UNVERIFIED
    # after verification, if support sufficient -> VERIFIED
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.VERIFIED


def test_contradictory_evidence_is_visible():
    eng = KnowledgeEngine(verification_threshold=0.7)
    c = eng.add_claim("contradictory claim")
    eng.add_evidence(c.claim_id, _ev("supports", 1.0))
    eng.add_evidence(c.claim_id, _ev("contradicts", -1.0))
    assert c.status is ClaimStatus.CONTRADICTORY
    assert (c.claim_id, c.statement) in eng.contradictions()
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.UNVERIFIED  # conflict blocks verification


def test_provenance_is_preserved():
    eng = KnowledgeEngine()
    s1 = _src("experiment")
    s2 = _src("document")
    eng.register_source(s1)
    eng.register_source(s2)
    c = eng.add_claim("provenance claim")
    e1 = _ev("first", 0.8, src=s1)
    e2 = _ev("second", 0.7, src=s2)
    eng.add_evidence(c.claim_id, e1)
    eng.add_evidence(c.claim_id, e2)
    assert c.provenance.evidence_ids == (e1.evidence_id, e2.evidence_id)
    assert c.provenance.source_ids == ("src-experiment-0.8", "src-document-0.8")


def test_unsupported_evidence_low():
    eng = KnowledgeEngine()
    c = eng.add_claim("weak claim")
    eng.add_evidence(c.claim_id, _ev("weak support", 0.1, reliability=0.2))
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.UNVERIFIED
    assert c.status in (ClaimStatus.UNSUPPORTED, ClaimStatus.UNCERTAIN)


def test_stale_knowledge_is_outdated():
    ttl = timedelta(seconds=1)
    eng = KnowledgeEngine(freshness_ttl=ttl)
    c = eng.add_claim("stale claim")
    old = datetime.now(timezone.utc) - timedelta(days=30)
    e = Evidence(
        content="old", support=1.0, reliability=0.9, source=_src(),
        captured_at=old,
    )
    eng.add_evidence(c.claim_id, e)
    eng.verify(c.claim_id)
    assert c.status is ClaimStatus.OUTDATED
    assert c.verification is VerificationStatus.UNVERIFIED


def test_evidence_fusion_raises_uncertainty_on_conflict():
    eng = KnowledgeEngine()
    c = eng.add_claim("fusion claim")
    eng.add_evidence(c.claim_id, _ev("pro", 1.0, reliability=0.9))
    eng.add_evidence(c.claim_id, _ev("con", -1.0, reliability=0.9))
    # conflicting evidence -> high uncertainty
    assert c.confidence.uncertainty >= 0.4


def test_source_reputation_updates():
    eng = KnowledgeEngine()
    s = _src("experiment", rep=0.5)
    eng.register_source(s)
    r1 = eng.update_source_reputation(s.identifier, verified=True)
    assert r1 > 0.5
    r2 = eng.update_source_reputation(s.identifier, verified=False)
    assert r2 < r1


def test_retrieval_returns_matching_verified_first():
    eng = KnowledgeEngine()
    a = eng.add_claim("the capital of France is Paris")
    eng.add_evidence(a.claim_id, _ev("atlas", 1.0))
    eng.verify(a.claim_id)
    b = eng.add_claim("the capital of France is Lyon")
    eng.add_evidence(b.claim_id, _ev("rumor", 0.3, reliability=0.2))
    eng.add_claim("unrelated topic")
    hits = eng.retrieve("capital of France")
    assert len(hits) == 2
    assert hits[0].claim_id == a.claim_id  # verified first


def test_unknown_claim_raises():
    eng = KnowledgeEngine()
    try:
        eng.get_claim("nope")
    except Exception as exc:
        assert "nope" in str(exc)
    else:
        raise AssertionError("expected ClaimNotFoundError")
