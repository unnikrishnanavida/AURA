"""Memory domain models.

Every memory entry distinguishes fact confidence, source reliability,
freshness, and relevance, and carries structured provenance so its origin is
always recoverable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import ExecutionId, MemoryId


class MemoryType(StrEnum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class LinkKind(StrEnum):
    CAUSAL = "causal"
    SIMILARITY = "similarity"
    TEMPORAL = "temporal"
    SHARED_GOAL = "shared_goal"
    SHARED_OUTCOME = "shared_outcome"


@dataclass(frozen=True, slots=True)
class Provenance:
    source: str
    execution_id: ExecutionId | None = None
    creator: str = "aura"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryConfidence:
    """Multi-axis confidence: fact, source, freshness, relevance."""

    fact: float = 0.5
    source: float = 0.5
    freshness: float = 0.5
    relevance: float = 0.5

    def __post_init__(self) -> None:
        for axis in (self.fact, self.source, self.freshness, self.relevance):
            if not 0.0 <= axis <= 1.0:
                raise ValueError(f"confidence axes must be in [0,1], got {axis}")

    @property
    def combined(self) -> float:
        return self.fact * 0.4 + self.source * 0.25 + self.freshness * 0.15 + self.relevance * 0.2


@dataclass
class MemoryEntry:
    id: MemoryId
    key: str
    kind: MemoryType
    content: dict[str, Any]
    importance: float = field(default=0.5)
    confidence: MemoryConfidence = field(default_factory=MemoryConfidence)
    provenance: Provenance = field(default_factory=lambda: Provenance(source="manual"))
    created_at: datetime = field(default_factory=lambda: SystemClock().now())
    last_access: datetime = field(default_factory=lambda: SystemClock().now())
    access_count: int = 0
    tags: tuple[str, ...] = ()
    expires_at: datetime | None = None
    links: dict[str, LinkKind] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(f"importance must be in [0,1], got {self.importance}")

    @classmethod
    def create(
        cls,
        *,
        key: str,
        kind: MemoryType,
        content: dict[str, Any],
        importance: float = 0.5,
        confidence: MemoryConfidence | None = None,
        provenance: Provenance | None = None,
        clock: Clock | None = None,
        expires_at: datetime | None = None,
        tags: tuple[str, ...] = (),
        memory_id: MemoryId | None = None,
    ) -> MemoryEntry:
        now = (clock or SystemClock()).now()
        return cls(
            id=memory_id or MemoryId.new(),
            key=key,
            kind=kind,
            content=content,
            importance=importance,
            confidence=confidence or MemoryConfidence(),
            provenance=provenance or Provenance(source="manual"),
            created_at=now,
            last_access=now,
            expires_at=expires_at,
            tags=tags,
        )

    def touch(self, clock: Clock | None = None) -> None:
        self.last_access = (clock or SystemClock()).now()
        self.access_count += 1

    def expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and self.expires_at < (now or SystemClock().now())


__all__ = ["LinkKind", "MemoryConfidence", "MemoryEntry", "MemoryType", "Provenance"]