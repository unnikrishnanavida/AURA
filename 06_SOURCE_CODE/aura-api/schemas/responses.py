"""Response envelopes and schema helpers for aura-api.

Every response is wrapped in a stable envelope carrying the correlation ID,
so consumers always have a consistent shape and cross-system traceability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResponseEnvelope:
    """Stable JSON envelope for all AURA API responses."""

    data: Any = None
    correlation_id: str = ""
    meta: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "correlation_id": self.correlation_id,
            "meta": self.meta or {},
        }


def ok(data: Any, *, correlation_id: str, **meta: Any) -> dict[str, Any]:
    """Build a successful response envelope."""
    return ResponseEnvelope(data=data, correlation_id=correlation_id, meta=meta or None).to_dict()


def paginated(items: list[Any], *, total: int, offset: int, limit: int, correlation_id: str) -> dict[str, Any]:
    """Build a paginated response envelope."""
    return ok(
        items,
        correlation_id=correlation_id,
        total=total,
        offset=offset,
        limit=limit,
    )


__all__ = ["ResponseEnvelope", "ok", "paginated"]