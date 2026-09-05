"""Memory access policy and lifecycle management.

Privacy and hygiene are modeled explicitly instead of leaked into the engine:

* :class:`MemoryPolicy` maps sensitivity classifications to clearance levels and
  refuses access below the required clearance.
* :func:`correct_entry` performs a versioned correction: the old record is
  marked ``SUPERSEDED`` (kept for provenance) and a new version is written that
  records what it supersedes.
* :class:`MemoryLifecycle` orchestrates corrections, retention purge, and
  lineage pruning to honor ``max_versions``.

Nothing in this module imports web/UI/security infrastructure so the
``domain -> infrastructure`` dependency direction is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import MemoryId
from aura.memory.engine import MemoryEngine
from aura.memory.models import (
    MemoryConfidence,
    MemoryEntry,
    MemoryStatus,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)

# Clearance levels are ordinal ranks: PUBLIC(0) < INTERNAL(1) < SENSITIVE(2)
# < RESTRICTED(3). A caller must hold clearance >= the classification rank of
# the record it touches.
_CLEARANCE_RANK = {
    Sensitivity.PUBLIC: 0,
    Sensitivity.INTERNAL: 1,
    Sensitivity.SENSITIVE: 2,
    Sensitivity.RESTRICTED: 3,
}


@dataclass(frozen=True, slots=True)
class AccessDecision:
    allowed: bool
    reason: str
    required_clearance: int
    held_clearance: int

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "required_clearance": self.required_clearance,
            "held_clearance": self.held_clearance,
        }
class MemoryPolicy:
    """Declarative access policy over memory sensitivity levels."""

    def can_access(self, sensitivity: Sensitivity, clearance: int | None) -> AccessDecision:
        """A caller with ``clearance`` may touch records of ``sensitivity``.

        ``clearance=0`` (anonymous) may only touch PUBLIC records. ``None``
        clearance defaults to 0 (deny by default).
        """
        held = clearance if clearance is not None else 0
        required = _CLEARANCE_RANK[sensitivity]
        if held < required:
            return AccessDecision(
                allowed=False,
                reason=(
                    f"clearance {held} below required {required} "
                    f"for {sensitivity.value!r} memory"
                ),
                required_clearance=required,
                held_clearance=held,
            )
        return AccessDecision(
            allowed=True,
            reason="clearance satisfied",
            required_clearance=required,
            held_clearance=held,
        )

    def require(self, sensitivity: Sensitivity, clearance: int | None) -> None:
        decision = self.can_access(sensitivity, clearance)
        if not decision.allowed:
            raise PermissionError(decision.reason)


@dataclass(frozen=True, slots=True)
class Correction:
    """Outcome of a versioned memory correction."""

    previous: MemoryEntry
    current: MemoryEntry

    def to_dict(self) -> dict[str, object]:
        return {
            "previous_id": str(self.previous.id),
            "current_id": str(self.current.id),
            "version": self.current.version,
            "provenance": f"{self.current.provenance.source}/{self.current.provenance.creator}",
        }


def correct_entry(
    entry: MemoryEntry,
    *,
    content: dict[str, Any],
    provenance: Provenance,
    clock: Clock | None = None,
    importance: float | None = None,
    confidence: MemoryConfidence | None = None,
) -> MemoryEntry:
    """Create the successor of ``entry`` and mark the predecessor superseded.

    The predecessor is never deleted: provenance requires that history survive.
    The successor inherits key/kind/tags/sensitivity/retention/expiry and links,
    and records ``supersedes`` so the lineage is traceable end to end.
    """
    if entry.status is MemoryStatus.SUPERSEDED:
        raise ValueError(f"cannot correct superseded memory {entry.id}")
    now = (clock or SystemClock()).now()
    entry.status = MemoryStatus.SUPERSEDED
    successor = MemoryEntry(
        id=MemoryId.new(),
        key=entry.key,
        kind=entry.kind,
        content=content,
        importance=importance if importance is not None else entry.importance,
        confidence=confidence or entry.confidence,
        provenance=provenance,
        created_at=now,
        last_access=now,
        tags=entry.tags,
        expires_at=entry.expires_at,
        links=dict(entry.links),
        sensitivity=entry.sensitivity,
        status=MemoryStatus.ACTIVE,
        version=entry.version + 1,
        supersedes=entry.id,
        observed_at=now,
        retention=entry.retention,
    )
    return successor
class MemoryLifecycle:
    """Versioned correction, retention purge, and lineage pruning."""

    def __init__(self, engine: MemoryEngine, *, policy: MemoryPolicy | None = None, clock: Clock | None = None) -> None:
        self.engine = engine
        self.policy = policy or MemoryPolicy()
        self._clock = clock or SystemClock()

    def correct(
        self,
        memory_id: MemoryId,
        *,
        content: dict[str, Any],
        provenance: Provenance,
        clearance: int | None = None,
    ) -> Correction:
        """Correct a memory record behind the sensitivity-access gate."""
        previous = self.engine.by_id(memory_id)
        self.policy.require(previous.sensitivity, clearance)
        successor = correct_entry(previous, content=content, provenance=provenance, clock=self._clock)
        self.engine.store.add(successor)
        self.engine.graph.register(successor)
        return Correction(previous=previous, current=successor)

    def purge_expired(self, now: datetime | None = None) -> list[MemoryId]:
        """Remove records expired by absolute or retention expiry."""
        removed: list[MemoryId] = []
        for entry in list(self.engine.store.all()):
            if entry.status is MemoryStatus.ACTIVE and entry.expired_by_retention(now or self._clock.now()):
                entry.status = MemoryStatus.EXPIRED
                self.engine.store.delete(entry.id)
                removed.append(entry.id)
        return removed

    def prune_lineage(self, root: MemoryEntry, *, retention: RetentionPolicy | None = None) -> list[MemoryId]:
        """Enforce ``max_versions``: purge the oldest superseded ancestors.

        The newest ``max_versions`` records of the lineage survive; the current
        record is always included, so everything older than the keep-window is
        pruned from the store (marked DELETED).
        """
        policy = retention or root.retention
        limit = policy.max_versions if policy else 1
        lineage = self._lineage(root)
        pruned: list[MemoryId] = []
        # lineage is oldest -> newest; keep the newest `limit` records
        keep_from = max(0, len(lineage) - limit)
        survivor_ids = {str(e.id) for e in (lineage[keep_from:] if limit > 0 else ())}
        for ancestor in lineage:
            if str(ancestor.id) not in survivor_ids:
                ancestor.status = MemoryStatus.DELETED
                self.engine.store.delete(ancestor.id)
                pruned.append(ancestor.id)
        return pruned

    def _lineage(self, root: MemoryEntry) -> list[MemoryEntry]:
        chain: list[MemoryEntry] = []
        cursor: MemoryEntry | None = root
        seen: set[str] = set()
        while cursor is not None and str(cursor.id) not in seen:
            seen.add(str(cursor.id))
            chain.append(cursor)
            if cursor.supersedes is None:
                break
            try:
                cursor = self.engine.store.get(cursor.supersedes)
            except Exception:
                break
        return list(reversed(chain))


__all__ = ["AccessDecision", "Correction", "MemoryLifecycle", "MemoryPolicy", "correct_entry"]