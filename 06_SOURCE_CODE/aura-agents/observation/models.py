"""Observation domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import ExecutionId

__all__ = ["Observation"]


@dataclass(frozen=True)
class Observation:
    """A recorded observation of what the system believes is true.

    ``state`` is an explicit dict of observed world-state variables; it is
    NEVER merged with action inputs. ``signals`` hold qualitative indicators
    extracted from sources. Confidence expresses the observer's certainty.
    """

    source: str
    state: dict[str, Any]
    signals: list[str] = field(default_factory=list)
    confidence: float = 1.0
    execution_id: ExecutionId | None = None
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
