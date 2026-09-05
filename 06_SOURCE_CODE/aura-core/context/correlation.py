"""Correlation context for aura-core.

Every cross-component operation carries a correlation ID so logs, traces, and
audit records can be correlated end-to-end.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def new_correlation_id() -> str:
    return f"co-{uuid.uuid4().hex[:16]}"


@dataclass
class CorrelationContext:
    """Immutable-ish correlation state for one logical operation."""

    correlation_id: str = field(default_factory=new_correlation_id)
    parent_id: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    def child(self, **props: Any) -> CorrelationContext:
        return CorrelationContext(
            correlation_id=self.correlation_id,
            parent_id=self.correlation_id,
            properties=self.properties,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "parent_id": self.parent_id,
            "properties": dict(self.properties),
        }


__all__ = ["CorrelationContext", "new_correlation_id"]