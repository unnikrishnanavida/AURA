"""Knowledge domain tests: claims, evidence, sources, verification, trust, contradictions."""

from __future__ import annotations

import pytest

from aura.foundation.errors import NotFoundError
from aura.knowledge.contradictions import ContradictionDetector
from aura.knowledge.engine import KnowledgeBase
from aura.knowledge.models import Claim, Evidence, Source, VerificationStatus


def make_source(name: str = "src", reliability: float = 0.9) -> Source:
    return Source(id=name, reliability=reliability)


def make_evidence(content: str, quality: float = 0.8, reliability: float = 0.9) -> Evidence:
    return Evidence(content=content, source=make_source(reliability=reliability), quality=quality)


def test_claim_create() -> None:
    claim = Claim.create(statement="the sky is blue", predicate=("sky", "color"))
    assert claim.statement == "the sky is blue"
    assert claim.predicate == ("sky", "color")


def test_add_and_get_claim() -> None:
    kb = KnowledgeBase()
    claim = Claim.create(statement="water boils at 100 C")
    kb.add(claim)
    assert kb.get(claim.id).statement == claim.statement


def test_get_missing_claim_raises() -> None:
    kb = KnowledgeBase()
    from aura.foundation.ids import ClaimId

    with pytest.raises(NotFoundError):
        kb.get(ClaimId.new())


def test_verify_unverified_without_evidence() -> None:
    kb = KnowledgeBase()
    claim = Claim.create(statement="unchecked claim")
    kb.add(claim)
    assert kb.verify(claim.id) is VerificationStatus.UNVERIFIED


def test_verify_with_evidence() -> None:
    kb = KnowledgeBase()
    claim = Claim.create(statement="verified claim")
    claim.with_evidence(make_evidence("direct observation"))
    kb.add(claim)
    assert kb.verify(claim.id) is VerificationStatus.VERIFIED


def test_evidence_increases_confidence() -> None:
    claim = Claim.create(statement="empirically supported")
    before = claim.confidence
    claim.with_evidence(make_evidence("replicated experiment", quality=0.9))
    assert claim.confidence > before
    assert claim.confidence <= 1.0


def test_retrieve_by_predicate() -> None:
    kb = KnowledgeBase()
    kb.add(Claim.create(statement="mars has two moons", predicate=("mars", "moons")))
    kb.add(Claim.create(statement="venus has none", predicate=("venus", "moons")))
    results = kb.retrieve(predicate=("mars", "moons"))
    assert len(results) == 1
    assert results[0][0].statement == "mars has two moons"


def test_retrieve_by_statement_fragment() -> None:
    kb = KnowledgeBase()
    kb.add(Claim.create(statement="the atmosphere of mars is thin"))
    results = kb.retrieve(statement="atmosphere")
    assert len(results) == 1


def test_trust_ranks_sources() -> None:
    kb = KnowledgeBase()
    trusted = Claim.create(statement="peer-reviewed finding")
    trusted.with_evidence(make_evidence("study", quality=0.9, reliability=0.95))
    dubious = Claim.create(statement="rumor")
    dubious.with_evidence(make_evidence("hearsay", quality=0.1, reliability=0.1))
    kb.add(trusted)
    kb.add(dubious)
    results = kb.retrieve()
    assert results[0][0].statement == "peer-reviewed finding"


def test_contradiction_detection() -> None:
    detector = ContradictionDetector()
    left = Claim.create(statement="the door is open", predicate=("door", "state"))
    right = Claim.create(statement="the door is not open", predicate=("door", "state"))
    found = detector.detect([left, right])
    assert len(found) == 1
    assert found[0].basis.startswith("predicate")


def test_same_polarity_is_not_contradiction() -> None:
    detector = ContradictionDetector()
    left = Claim.create(statement="the door is open", predicate=("door", "state"))
    right = Claim.create(statement="the door is ajar", predicate=("door", "state"))
    assert detector.detect([left, right]) == []


def test_health_report() -> None:
    kb = KnowledgeBase()
    assert kb.health()["status"] == "ok"
    kb.add(Claim.create(statement="thing"))
    assert kb.health()["claims"] == 1