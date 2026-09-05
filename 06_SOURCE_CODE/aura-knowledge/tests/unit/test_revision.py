"""Unit tests for belief revision and knowledge lineage in aura-knowledge.

Refutation, source reputation, provenance lineage, and claim-to-evidence
relationships must all be representable and never silently lost.
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


def _src(identifier="s"):
    return Source(identifier=identifier, reputation=0.8)


def test_refute_marks_unsupported():
    engine = KnowledgeEngine()
    c = engine.add_claim("refutable claim")
    engine.refute(c.claim_id, reason="contrary evidence verified")
    assert c.verification is VerificationStatus.REFUTED
    assert c.status is ClaimStatus.UNSUPPORTED
    assert c.metadata["refutation_reason"] == "contrary evidence verified"


def test_provenance_lineage_accumulates():
    engine = KnowledgeEngine()
    engine.register_source(_src("exp"))
    engine.register_source(_src("doc"))
    c = engine.add_claim("lineage claim")
    e1 = Evidence(content="first", support=0.8, reliability=0.9, source=_src("exp"))
    e2 = Evidence(content="second", support=0.7, reliability=0.9, source=_src("doc"))
    engine.add_evidence(c.claim_id, e1)
    engine.add_evidence(c.claim_id, e2)
    assert e1.evidence_id in c.provenance.evidence_ids
    assert e2.evidence_id in c.provenance.evidence_ids
    assert "exp" in c.provenance.source_ids
    assert "doc" in c.provenance.source_ids


def test_claim_to_evidence_relationship():
    engine = KnowledgeEngine()
    c = engine.add_claim("claim with evidence")
    e = Evidence(content="supporting", support=1.0, reliability=0.9, source=_src())
    engine.add_evidence(c.claim_id, e)
    assert c.evidence[0].evidence_id == e.evidence_id
    assert c.has_evidence is True


def test_duplicate_evidence_is_deduplicated():
    engine = KnowledgeEngine()
    c = engine.add_claim("dedup claim")
    e = Evidence(content="once", support=1.0, reliability=0.9, source=_src())
    engine.add_evidence(c.claim_id, e)
    engine.add_evidence(c.claim_id, e)
    assert len(c.evidence) == 1


def test_unknown_claim_raises():
    engine = KnowledgeEngine()
    try:
        engine.get_claim("missing-id")
    except Exception as exc:  # noqa: BLE001
        assert "missing-id" in str(exc)
    else:
        raise AssertionError("expected ClaimNotFoundError")