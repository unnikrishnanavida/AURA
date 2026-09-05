"""AURA research.

Structured, evidence-aware research: question decomposition, claim
passports, epistemic ledger, evidence provenance, hypotheses, synthesis,
and reproducibility capsules.
"""

from __future__ import annotations

from aura.research.engine import ResearchEngine, ResearchOutput
from aura.research.ledger import ClaimPassport, EpistemicLedger, LedgerEntry
from aura.research.models import (
    EpistemicStatus,
    Finding,
    ReproducibilityCapsule,
    ResearchInput,
    ResearchQuestion,
    SourceQuality,
)

__all__ = [
    "ClaimPassport",
    "EpistemicLedger",
    "EpistemicStatus",
    "Finding",
    "LedgerEntry",
    "ReproducibilityCapsule",
    "ResearchEngine",
    "ResearchInput",
    "ResearchOutput",
    "ResearchQuestion",
    "SourceQuality",
]