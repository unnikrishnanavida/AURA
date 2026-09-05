"""Unit tests for the aura-knowledge verification boundary.

Verification and confidence are distinct axes. An unverified source cannot
promote a claim to VERIFIED knowledge; unsupported claims must never become
verified knowledge.
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


def _src(identifier="peer", rep=0.8):
    return Source(identifier=identifier, reputation=rep)


def test_unverified_source_cannot_verify():
    """Strong evidence from an unverified/low-reputation source stays UNVERIFIED."""
    eng = KnowledgeEngine(verification_threshold=0.9)
    c = eng.add_claim("the sky is green")
    eng.add_evidence(
        c.claim_id,
        Evidence(content="claimed by peer", support=1.0, reliability=0.9, source=_src("peer", rep=0.1)),
    )
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.UNVERIFIED
    assert c.status is not ClaimStatus.SUPPORTED


def test_confidence_without_verification_is_not_knowledge():
    eng = KnowledgeEngine()
    c = eng.add_claim("plausible but unchecked")
    eng.add_evidence(c.claim_id, Evidence(content="suggestion", support=0.95, reliability=0.95, source=_src()))
    assert c.confidence is not None and c.confidence.value >= 0.8
    # confidence is high but there has been no explicit verification step
    assert c.verification is VerificationStatus.UNVERIFIED
    result = eng.retrieve("plausible")[0]
    assert result.known is False
    assert result.says_unknown is True


def test_explicit_verify_promotes_supported_claim():
    eng = KnowledgeEngine()
    c = eng.add_claim("a verified fact")
    eng.add_evidence(
        c.claim_id,
        Evidence(content="official record", support=1.0, reliability=0.95, source=_src()),
    )
    # evidence alone must not auto-verify
    assert c.verification is VerificationStatus.UNVERIFIED
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.VERIFIED
    assert c.status is ClaimStatus.SUPPORTED


def test_refuted_claim_cannot_be_verified():
    eng = KnowledgeEngine()
    c = eng.add_claim("a claim that was refuted")
    eng.refute(c.claim_id, reason="contrary evidence verified")
    assert c.verification is VerificationStatus.REFUTED
    eng.verify(c.claim_id)
    assert c.verification is VerificationStatus.REFUTED