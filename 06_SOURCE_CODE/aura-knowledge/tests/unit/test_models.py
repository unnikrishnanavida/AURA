"""Unit tests for aura-knowledge domain models.

Covers the epistemic invariants: first-class uncertainty, immutability of
provenance, validation of Source/Evidence/Confidence ranges, and the
distinction between confidence and verification.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_knowledge import Confidence, Evidence, Source
from aura_knowledge.core.models import Claim, KnowledgeResult, VerificationStatus


def test_source_validation():
    with pytest.raises(ValueError):
        Source(identifier=" ", reputation=0.5)
    with pytest.raises(ValueError):
        Source(identifier="s1", reputation=1.5)
    with pytest.raises(ValueError):
        Source(identifier="s1", reputation=-0.1)


def test_evidence_validation():
    with pytest.raises(ValueError):
        Evidence(content="c", support=2.0)
    with pytest.raises(ValueError):
        Evidence(content="c", support=0.0, reliability=3.0)


def test_evidence_mode_direction():
    assert Evidence(content="a", support=1.0).mode.value == "support"
    assert Evidence(content="a", support=-1.0).mode.value == "contradict"
    assert Evidence(content="a", support=0.0).mode.value == "support"


def test_confidence_validation_and_first_class_uncertainty():
    c = Confidence(value=0.9, uncertainty=0.4)
    assert c.value == 0.9
    assert c.uncertainty == 0.4
    with pytest.raises(ValueError):
        Confidence(value=1.2, uncertainty=0.0)
    with pytest.raises(ValueError):
        Confidence(value=0.5, uncertainty=-0.1)


def test_confidence_is_not_verification():
    """High confidence without verification must not imply verified."""
    claim = Claim(statement="strong but unchecked")
    assert claim.confidence is None
    assert claim.verification is VerificationStatus.UNVERIFIED


def test_claim_requires_statement():
    with pytest.raises(ValueError):
        Claim(statement="")


def test_provenance_is_immutable():
    from aura_knowledge import Provenance

    p = Provenance(claim_id="cl-1", created_by="tester")
    with pytest.raises(AttributeError):
        p.evidence_ids = ("ev-9",)  # type: ignore[misc]


def test_knowledge_result_unknown_signal():
    """AURA's first-class 'I do not know' must be representable."""
    claim = Claim(statement="unverified")
    result = KnowledgeResult(claim=claim, trust=0.0)
    assert result.says_unknown is True
    assert result.known is False
    assert result.to_dict()["known"] is False