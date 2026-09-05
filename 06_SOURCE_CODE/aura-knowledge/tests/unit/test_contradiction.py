"""Unit tests for contradiction detection in aura-knowledge.

Contradictory evidence must remain visible, and conflict must block
verification: the engine never hides a disagreement behind a single score.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import (
    Claim,
    ClaimStatus,
    ContradictionDetector,
    Evidence,
    KnowledgeEngine,
    Source,
    VerificationStatus,
)


def _src(rep=0.8):
    return Source(identifier=f"src-{rep}", reputation=rep)


def test_inter_claim_conflict_detected():
    eng = KnowledgeEngine()
    a = eng.add_claim("the sky is blue", predicate=("sky", "color"))
    b = eng.add_claim("the sky is not blue", predicate=("sky", "color"))
    conflicts = eng.contradictions()
    assert any(c.first_claim_id in (a.claim_id, b.claim_id) for c in conflicts)


def test_intra_claim_conflict_visible_and_blocks_verification():
    eng = KnowledgeEngine(verification_threshold=0.7)
    c = eng.add_claim("a contradictory claim")
    eng.add_evidence(c.claim_id, Evidence(content="for", support=1.0, reliability=0.9, source=_src()))
    eng.add_evidence(c.claim_id, Evidence(content="against", support=-1.0, reliability=0.9, source=_src()))
    assert c.status is ClaimStatus.CONTRADICTORY
    assert (c.claim_id, c.statement) in eng.contradictions()
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.UNVERIFIED


def test_same_polarity_claims_do_not_conflict():
    detector = ContradictionDetector()
    a = Claim(statement="the sky is blue", predicate=("sky", "color"))
    b = Claim(statement="the sky is also blue", predicate=("sky", "color"))
    assert detector.detect_claims([a, b]) == []


def test_unrelated_predicates_do_not_conflict():
    detector = ContradictionDetector()
    a = Claim(statement="the sky is blue", predicate=("sky", "color"))
    b = Claim(statement="the sky is not blue", predicate=("weather", "rain"))
    assert detector.detect_claims([a, b]) == []


def test_conflict_evidence_raises_uncertainty():
    eng = KnowledgeEngine()
    c = eng.add_claim("uncertain claim")
    eng.add_evidence(c.claim_id, Evidence(content="pro", support=1.0, reliability=0.9, source=_src()))
    eng.add_evidence(c.claim_id, Evidence(content="con", support=-1.0, reliability=0.9, source=_src()))
    assert c.confidence is not None
    assert c.confidence.uncertainty >= 0.4