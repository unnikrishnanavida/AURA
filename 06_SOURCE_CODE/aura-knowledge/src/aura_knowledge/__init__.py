"""AURA Knowledge - claims, evidence, sources, provenance, verification, trust.

A serious knowledge and evidence subsystem. The conceptual model:

    CLAIM -> EVIDENCE -> SOURCE -> PROVENANCE -> VERIFICATION
    -> CONFIDENCE + UNCERTAINTY -> KNOWLEDGE STATE

Knowledge states: supported, unsupported, uncertain, contradictory,
outdated, unverified. Verification and confidence are distinct.
Uncertainty is first-class.
"""

from __future__ import annotations

from aura_knowledge.contradiction import Contradiction, ContradictionDetector
from aura_knowledge.core.engine import KnowledgeEngine
from aura_knowledge.core.errors import (
    ClaimNotFoundError,
    EvidenceNotFoundError,
    KnowledgeError,
    SourceNotFoundError,
    UnsupportedOperationError,
    ValidationError,
    VerificationBlockedError,
)
from aura_knowledge.core.models import (
    Claim,
    ClaimStatus,
    Confidence,
    Evidence,
    EvidenceMode,
    KnowledgeResult,
    Provenance,
    Source,
    SourceKind,
    VerificationStatus,
)
from aura_knowledge.freshness import FreshnessEngine
from aura_knowledge.fusion import EvidenceFusion
from aura_knowledge.trust import TrustModel

__all__ = [
    "Claim",
    "ClaimNotFoundError",
    "ClaimStatus",
    "Confidence",
    "Contradiction",
    "ContradictionDetector",
    "Evidence",
    "EvidenceFusion",
    "EvidenceMode",
    "EvidenceNotFoundError",
    "FreshnessEngine",
    "KnowledgeEngine",
    "KnowledgeError",
    "KnowledgeResult",
    "Provenance",
    "Source",
    "SourceKind",
    "SourceNotFoundError",
    "TrustModel",
    "UnsupportedOperationError",
    "ValidationError",
    "VerificationBlockedError",
    "VerificationStatus",
]