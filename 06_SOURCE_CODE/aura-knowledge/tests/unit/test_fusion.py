"""Unit tests for evidence fusion in aura-knowledge.

Fusion combines evidence into confidence + uncertainty. Conflicts raise
uncertainty rather than being averaged away; absence of evidence yields zero
confidence and full uncertainty.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_knowledge import Confidence, Evidence, EvidenceFusion, Source


def _ev(support, reliability=0.9, rep=0.8):
    return Evidence(
        content="e",
        support=support,
        reliability=reliability,
        source=Source(identifier="s", reputation=rep),
    )


def test_no_evidence_full_uncertainty():
    result = EvidenceFusion().fuse([])
    assert isinstance(result, Confidence)
    assert result.value == 0.0
    assert result.uncertainty == 1.0


def test_agreement_gives_high_confidence_low_uncertainty():
    result = EvidenceFusion().fuse([_ev(1.0), _ev(1.0), _ev(0.9)])
    assert result.value >= 0.8
    assert result.uncertainty < 0.5


def test_conflict_raises_uncertainty():
    agreeing = EvidenceFusion().fuse([_ev(1.0), _ev(1.0)])
    conflicting = EvidenceFusion().fuse([_ev(1.0), _ev(-1.0)])
    assert conflicting.uncertainty > agreeing.uncertainty


def test_confidence_bounded_to_unit_interval():
    fusion = EvidenceFusion()
    for support in (-1.0, -0.5, 0.0, 0.5, 1.0):
        result = fusion.fuse([_ev(support)])
        assert 0.0 <= result.value <= 1.0
        assert 0.0 <= result.uncertainty <= 1.0