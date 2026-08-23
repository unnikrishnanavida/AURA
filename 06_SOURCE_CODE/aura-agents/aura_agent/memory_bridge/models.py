"""Memory bridge models: episodic/semantic/experience memory contracts.

The bridge defines the Agent <-> AURA Memory integration boundary. It never
stores shared global state; a provider is injected at runtime. In-memory and
adapter implementations can be swapped without touching consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

__all__ = ["MemoryEntry", "Experience", "MemoryQuery", "MemoryRecord"]


@dataclass(frozen=True)
class MemoryEntry:
    """A retrievable memory item."""

    key: str
    kind: str  # "episodic" | "semantic" | "experience" | "outcome" | "reflection"
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None


@dataclass(frozen=True)
class Experience:
    """A learned experience: what was done and whether it worked."""

    action: str
    succeeded: bool
    context: dict[str, Any] = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class MemoryQuery:
    """A retrieval query."""

    kind: str = "*"
    key: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class MemoryRecord:
    """A search hit with relevance metadata."""

    entry: MemoryEntry
    score: float = 0.0