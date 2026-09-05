"""End-to-end trust lifecycle test for aura-knowledge.

Walks the full conceptual pipeline required by the AURA ecosystem:

    CLAIM -> EVIDENCE -> SOURCE -> PROVENANCE -> VERIFICATION
    -> CONFIDENCE + UNCERTAINTY -> KNOWLEDGE STATE -> RETRIEVAL

Includes the first-class 'I do not know' path when evidence is insufficient.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import (
    ClaimStatus,
    Evidence,
    KnowledgeEngine,
    Source,
    VerificationStatus,
)


def test_full_trusted_knowledge_lifecycle():
    engine = KnowledgeEngine()

    # --- SOURCE ---
    atlas = Source(identifier="atlas", reputation=0.95)
    article = Source(identifier="article", reputation=0.7)
    engine.register_source(atlas)
    engine.register_source(article)

    # --- CLAIM ---
    claim = engine.add_claim("the capital of France is Paris", created_by="integration-test")

    # --- EVIDENCE ---
    engine.add_evidence(
        claim.claim_id,
        Evidence(content="geography textbook", support=1.0, reliability=0.95, source=atlas),
    )
    engine.add_evidence(
        claim.claim_id,
        Evidence(content="encyclopedia", support=0.9, reliability=0.8, source=article),
    )

    # --- PROVENANCE (never silently lost) ---
    assert len(claim.provenance.evidence_ids) == 2
    assert set(claim.provenance.source_ids) == {"atlas", "article"}
    assert claim.provenance.created_by == "integration-test"

    # --- VERIFICATION (explicit step) ---
    assert claim.verification is VerificationStatus.UNVERIFIED  # not auto-verified
    engine.verify(claim.claim_id)
    assert claim.verification is VerificationStatus.VERIFIED
    assert claim.status is ClaimStatus.SUPPORTED

    # --- CONFIDENCE + UNCERTAINTY ---
    assert claim.confidence is not None
    assert 0.0 <= claim.confidence.value <= 1.0
    assert 0.0 <= claim.confidence.uncertainty <= 1.0

    # --- RETRIEVAL ---
    results = engine.retrieve("capital of France")
    assert len(results) == 1
    top = results[0]
    assert top.known is True
    assert top.says_unknown is False
    assert top.to_dict()["claim_id"] == claim.claim_id


def test_lifecycle_insufficient_evidence_says_unknown():
    """When evidence is insufficient the system must say 'I do not know'."""
    engine = KnowledgeEngine(verification_threshold=0.7)
    rumour = Source(identifier="rumour", reputation=0.1)
    engine.register_source(rumour)
    claim = engine.add_claim("the capital of Mars is Olympus")
    engine.add_evidence(
        claim.claim_id,
        Evidence(content="unverified blog", support=0.2, reliability=0.1, source=rumour),
    )
    engine.verify(claim.claim_id)
    assert claim.verification is VerificationStatus.UNVERIFIED
    result = engine.retrieve("capital of Mars")[0]
    assert result.says_unknown is True
    assert result.known is False


def test_lifecycle_conflict_never_hides_contradiction():
    engine = KnowledgeEngine(verification_threshold=0.7)
    a = engine.add_claim("the sea level is rising", predicate=("climate", "sea_level"))
    b = engine.add_claim("the sea level is not rising", predicate=("climate", "sea_level"))
    engine.add_evidence(a.claim_id, Evidence(content="study A", support=1.0, reliability=0.9, source=Source("a", reputation=0.9)))
    engine.add_evidence(b.claim_id, Evidence(content="study B", support=1.0, reliability=0.9, source=Source("b", reputation=0.9)))
    conflicts = engine.contradictions()
    assert len(conflicts) >= 1
    # Both claims are visible; neither is silently declared winner
    hits = engine.retrieve("sea level")
    assert {h.claim_id for h in hits} == {a.claim_id, b.claim_id}