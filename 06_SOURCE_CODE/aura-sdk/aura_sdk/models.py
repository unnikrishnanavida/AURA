"""Typed request/response models for the SDK.

An :class:`SdkRequest` carries the operation name, payload, and trace context
(request id, trace id). An :class:`SdkResponse` always returns the matching ids
plus elapsed time, so observability never depends on the transport kind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import SdkError, SdkValidationError


@dataclass(frozen=True, slots=True)
class SdkRequest:
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    trace_id: str = ""
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.operation or not self.operation.strip():
            raise SdkValidationError("operation must be a non-empty string")
        if not isinstance(self.payload, dict):
            raise SdkValidationError("payload must be a mapping")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise SdkValidationError("timeout_seconds must be positive or None")


@dataclass(frozen=True, slots=True)
class SdkResponse:
    operation: str
    ok: bool
    payload: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    trace_id: str = ""
    duration_ms: float = 0.0
    error: SdkError | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "ok": self.ok,
            "payload": self.payload,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "duration_ms": round(self.duration_ms, 3),
            "error": self.error.to_dict() if self.error else None,
        }


__all__ = ["SdkRequest", "SdkResponse"]