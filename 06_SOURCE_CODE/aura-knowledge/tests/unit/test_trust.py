"""Unit tests for trust scoring and source reputation in aura-knowledge.

Trust is a composite of evidence quality, source reputation, freshness, and
verification. A claim with no evidence receives zero trust; an unverified
source depresses trust.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import (
    Claim,
    ClaimStatus,
    Evidence,
    KnowledgeEngine,
    Source,
    TrustModel,
    VerificationStatus,
)


def _src(identifier="s", rep=0.9):
    return Source(identifier=identifier, reputation=rep)


def test_no_evidence_zero_trust():
    engine = KnowledgeEngine()
    c = engine.add_claim("unsupported claim")
    assessment = engine.trust.assess(c)
    assert assessment["trust"] == 0.0
    assert assessment["source_reputation"] == 0.0


def test_verified_claim_trusts_higher_than_unverified():
    engine = KnowledgeEngine()
    a = engine.add_claim("checked claim")
    engine.add_evidence(a.claim_id, Evidence(content="e", support=1.0, reliability=0.9, source=_src()))
    engine.verify(a.claim_id)
    b = engine.add_claim("unchecked claim")
    engine.add_evidence(b.claim_id, Evidence(content="e", support=1.0, reliability=0.9, source=_src()))
    assert a.verification is VerificationStatus.VERIFIED
    trust_a = engine.trust.assess(a)["trust"]
    trust_b = engine.trust.assess(b)["trust"]
    assert trust_a > trust_b


def test_low_reputation_source_depresses_trust():
    engine = KnowledgeEngine()
    a = engine.add_claim("from reputable source")
    engine.add_evidence(a.claim_id, Evidence(content="e", support=1.0, reliability=0.9, source=_src("rep", rep=0.95)))
    b = engine.add_claim("from dubious source")
    engine.add_evidence(b.claim_id, Evidence(content="e", support=1.0, reliability=0.9, source=_src("dub", rep=0.1)))
    assert engine.trust.assess(a)["source_reputation"] > engine.trust.assess(b)["source_reputation"]


def test_source_reputation_updates_on_outcome():
    engine = KnowledgeEngine()
    s = Source(identifier="s", reputation=0.5)
    engine.register_source(s)
    up = engine.update_source_reputation("s", verified=True)
    assert up > 0.5
    down = engine.update_source_reputation("s", verified=False)
    assert down < up


def test_refuted_claim_gets_zero_trust():
    engine = KnowledgeEngine()
    c = engine.add_claim("refuted claim")
    engine.add_evidence(c.claim_id, Evidence(content="e", support=1.0, reliability=0.9, source=_src()))
    engine.refute(c.claim_id, reason="contradicted")
    assessment = engine.trust.assess(c)
    assert assessment["verification_multiplier"] == 0.0
    assert assessment["trust"] == 0.0


def test_trust_breaks_down_axes():
    model = TrustModel()
    c = Claim(statement="claim", evidence=[Evidence(content="e", support=1.0, reliability=0.9, source=_src())])
    assessment = model.assess(c)
    assert {"trust", "evidence_quality", "source_reputation", "freshness", "verification_multiplier"} <= set(assessment)