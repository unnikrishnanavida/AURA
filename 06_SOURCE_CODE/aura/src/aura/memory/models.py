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


class MemoryStatus(StrEnum):
    """Explicit lifecycle state of a memory record.

    :attr:`ACTIVE` records are retrievable. :attr:`SUPERSEDED` records were
    replaced by a newer version and are kept only for provenance. :attr:`ARCHIVED`
    records are moved out of the live store for retention and can be restored on
    demand. :attr:`DELETED` and :attr:`EXPIRED` are terminal states surfaced by
    the store/lifecycle layer.
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"


class Sensitivity(StrEnum):
    """Data sensitivity classification used to gate access to memory records.

    Order matches clearance levels: PUBLIC (0) < INTERNAL (1) < SENSITIVE (2)
    < RESTRICTED (3). RESTRICTED content must never leave the owning process
    without explicit policy.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


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


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Declarative retention for a memory record.

    ``ttl_seconds`` expresses relative expiry from ``created_at``. When combined
    with an absolute ``valid_until`` on the entry, the earlier boundary wins.
    ``max_versions`` limits how many superseded predecessors a record lineage may
    accumulate before the oldest are purged.
    """

    ttl_seconds: float | None = None
    max_versions: int = 1

    def __post_init__(self) -> None:
        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be positive, got {self.ttl_seconds}")
        if self.max_versions < 1:
            raise ValueError(f"max_versions must be >= 1, got {self.max_versions}")


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
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    status: MemoryStatus = MemoryStatus.ACTIVE
    version: int = 1
    supersedes: MemoryId | None = None
    observed_at: datetime | None = None
    retention: RetentionPolicy | None = None

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
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        observed_at: datetime | None = None,
        retention: RetentionPolicy | None = None,
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
            sensitivity=sensitivity,
            observed_at=observed_at,
            retention=retention,
        )

    def touch(self, clock: Clock | None = None) -> None:
        self.last_access = (clock or SystemClock()).now()
        self.access_count += 1

    def expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and self.expires_at < (now or SystemClock().now())

    def effective_expiry(self, now: datetime | None = None) -> datetime | None:
        """Earliest expiry among the absolute ``expires_at`` and retention TTL."""
        boundaries: list[datetime] = []
        if self.expires_at is not None:
            boundaries.append(self.expires_at)
        if self.retention is not None and self.retention.ttl_seconds is not None:
            from datetime import timedelta

            boundaries.append(self.created_at + timedelta(seconds=self.retention.ttl_seconds))
        if not boundaries:
            return None
        for boundary in boundaries:
            if boundary.tzinfo is None:
                # naive boundaries are interpreted as UTC to stay comparable
                from datetime import UTC

                boundary = boundary.replace(tzinfo=UTC)
        return min(boundaries)

    def expired_by_retention(self, now: datetime | None = None) -> bool:
        expiry = self.effective_expiry(now)
        return expiry is not None and expiry < (now or SystemClock().now())


__all__ = [
    "LinkKind",
    "MemoryConfidence",
    "MemoryEntry",
    "MemoryStatus",
    "MemoryType",
    "Provenance",
    "RetentionPolicy",
    "Sensitivity",
]