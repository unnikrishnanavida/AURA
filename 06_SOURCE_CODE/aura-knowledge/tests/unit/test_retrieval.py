"""Unit tests for retrieval ranking in aura-knowledge."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import Evidence, KnowledgeEngine, Source, VerificationStatus


def _src(rep=0.9):
    return Source(identifier="s", reputation=rep)


def test_retrieval_returns_matching_verified_first():
    eng = KnowledgeEngine()
    a = eng.add_claim("the capital of France is Paris")
    eng.add_evidence(a.claim_id, Evidence(content="atlas", support=1.0, reliability=0.9, source=_src()))
    eng.verify(a.claim_id)
    b = eng.add_claim("the capital of France is Lyon")
    eng.add_evidence(b.claim_id, Evidence(content="rumor", support=0.3, reliability=0.2, source=_src(rep=0.2)))
    eng.add_claim("unrelated topic")
    hits = eng.retrieve("capital of France")
    assert len(hits) == 2
    assert hits[0].claim_id == a.claim_id  # verified first


def test_retrieve_by_predicate():
    eng = KnowledgeEngine()
    a = eng.add_claim("alpha is greater", predicate=("math", "ordering"))
    eng.add_claim("some other topic", predicate=("history",))
    hits = eng.retrieve(predicate=("math", "ordering"))
    assert len(hits) == 1
    assert hits[0].claim_id == a.claim_id


def test_verified_only_filter():
    eng = KnowledgeEngine()
    a = eng.add_claim("verified fact")
    eng.add_evidence(a.claim_id, Evidence(content="record", support=1.0, reliability=0.95, source=_src()))
    eng.verify(a.claim_id)
    eng.add_claim("unverified claim")
    hits = eng.retrieve(verified_only=True)
    assert len(hits) == 1
    assert hits[0].claim_id == a.claim_id
    assert hits[0].claim.verification is VerificationStatus.VERIFIED


def test_retrieval_result_carries_uncertainty():
    eng = KnowledgeEngine()
    c = eng.add_claim("uncertain retrieval target")
    eng.add_evidence(c.claim_id, Evidence(content="pro", support=1.0, reliability=0.9, source=_src()))
    eng.add_evidence(c.claim_id, Evidence(content="con", support=-1.0, reliability=0.9, source=_src()))
    hits = eng.retrieve("uncertain retrieval target")
    assert len(hits) == 1
    result = hits[0]
    assert result.says_unknown is True
    assert "uncertainty" in result.to_dict()