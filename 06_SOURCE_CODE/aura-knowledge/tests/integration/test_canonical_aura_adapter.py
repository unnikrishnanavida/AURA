"""Integration tests: aura-knowledge bridges to the canonical AURA runtime.

The canonical ``aura`` package is installed as an editable dependency. These
tests prove that claims produced here can be consumed by the canonical
knowledge base/trust model without duplicating the engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_knowledge import Evidence, KnowledgeEngine, Source, VerificationStatus
from aura_knowledge.integrations.aura_canonical import BridgeUnavailable, from_canonical, to_canonical


@pytest.fixture
def canonical_ok():
    try:
        import aura  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif("not canonical_ok")
def test_bridge_to_canonical_preserves_id():
    engine = KnowledgeEngine()
    c = engine.add_claim("the capital of France is Paris")
    engine.add_evidence(
        c.claim_id,
        Evidence(content="atlas", support=1.0, reliability=0.95, source=Source("atlas", reputation=0.9)),
    )
    engine.verify(c.claim_id)
    canonical = to_canonical(c)
    assert str(canonical.id) == c.claim_id
    assert canonical.statement == c.statement
    assert canonical.confidence == pytest.approx(c.confidence.value)


@pytest.mark.skipif("not canonical_ok")
def test_canonical_knowledge_base_can_consume_bridge_claim():
    from aura.knowledge.engine import KnowledgeBase

    engine = KnowledgeEngine()
    c = engine.add_claim("bridge claim for canonical consumption")
    engine.add_evidence(
        c.claim_id,
        Evidence(content="e", support=1.0, reliability=0.9, source=Source("s", reputation=0.9)),
    )
    engine.verify(c.claim_id)
    kb = KnowledgeBase()
    kb.add(to_canonical(c))
    retrieved = kb.get(c.claim_id)
    assert retrieved.statement == c.statement


@pytest.mark.skipif("not canonical_ok")
def test_round_trip_preserves_verification():
    engine = KnowledgeEngine()
    c = engine.add_claim("round trip claim")
    engine.add_evidence(
        c.claim_id,
        Evidence(content="e", support=1.0, reliability=0.9, source=Source("s", reputation=0.9)),
    )
    engine.verify(c.claim_id)
    assert c.verification is VerificationStatus.VERIFIED
    back = from_canonical(to_canonical(c))
    assert back.claim_id == c.claim_id
    assert back.statement == c.statement
    assert back.verification is VerificationStatus.VERIFIED


@pytest.mark.skipif("canonical_ok")
def test_bridge_reports_unavailable_when_no_canonical():
    with pytest.raises(BridgeUnavailable):
        from_canonical(None)  # type: ignore[arg-type]