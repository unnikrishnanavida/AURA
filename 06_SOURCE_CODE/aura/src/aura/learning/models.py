"""Learning domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from aura.foundation.ids import new_hex


class SignalStatus(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"


@dataclass
class LearningSignal:
    id: str
    kind: str
    content: str
    evidence: list[dict[str, float]] = field(default_factory=list)  # [{"score": 0..1}]
    status: SignalStatus = SignalStatus.CANDIDATE
    safety_relevant: bool = False
    authorized: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        content: str,
        evidence: list[dict[str, float]] | None = None,
    ) -> LearningSignal:
        return cls(
            id=f"sig-{new_hex()}",
            kind=kind,
            content=content,
            evidence=evidence or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content": self.content,
            "status": self.status.value,
            "safety_relevant": self.safety_relevant,
            "authorized": self.authorized,
            "evidence_count": len(self.evidence),
        }


__all__ = ["LearningSignal", "SignalStatus"]