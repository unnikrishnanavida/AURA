"""Knowledge trust model.

Distinguishes CLAIM, EVIDENCE, SOURCE, VERIFICATION, and CONFIDENCE so
retrieved information is never treated as equally trustworthy.
"""

from __future__ import annotations

from aura.knowledge.contradictions import Contradiction, ContradictionDetector
from aura.knowledge.engine import KnowledgeBase
from aura.knowledge.models import (
    Claim,
    Evidence,
    KnowledgeResult,
    Source,
    VerificationStatus,
)
from aura.knowledge.trust import TrustModel

__all__ = [
    "Claim",
    "Contradiction",
    "ContradictionDetector",
    "Evidence",
    "KnowledgeBase",
    "KnowledgeResult",
    "Source",
    "TrustModel",
    "VerificationStatus",
]