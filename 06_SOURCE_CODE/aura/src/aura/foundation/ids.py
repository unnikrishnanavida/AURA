"""Canonical identifiers for the AURA platform.

Every cross-system identity is a typed value built on a deterministic
hexadecimal suffix. Prefixes keep ids readable in logs and support
reconstructing what kind of entity an id refers to.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import ClassVar, TypeVar

_IdT = TypeVar("_IdT", bound="_Id")


def new_hex(entropy: int = 8) -> str:
    """Return a hex digest string, defaulting to 8 bytes (16 hex chars)."""
    if entropy < 1:
        raise ValueError("entropy must be >= 1")
    return uuid.uuid4().hex[: entropy * 2]


@dataclass(frozen=True, slots=True)
class _Id:
    """Base typed id. Subclasses declare a prefix used in string form."""

    prefix: ClassVar[str] = "id"
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError(f"{type(self).__name__} value must not be empty")

    @classmethod
    def new(cls: type[_IdT]) -> _IdT:
        return cls(value=new_hex())

    @classmethod
    def from_str(cls: type[_IdT], token: str | _Id) -> _IdT:
        """Parse a string that may or may not carry the prefix (e.g. ``ex-abc``)."""
        if isinstance(token, _Id):
            return cls(value=token.value)
        text = str(token)
        prefix = cls.prefix + "-"
        if text.startswith(prefix):
            text = text[len(prefix) :]
        return cls(value=text)

    def __str__(self) -> str:
        return f"{self.prefix}-{self.value}"


class ExecutionId(_Id):
    prefix: ClassVar[str] = "ex"


class CorrelationId(_Id):
    prefix: ClassVar[str] = "co"


class EventId(_Id):
    prefix: ClassVar[str] = "ev"


class RequestId(_Id):
    prefix: ClassVar[str] = "rq"


class AgentId(_Id):
    prefix: ClassVar[str] = "ag"


class GoalId(_Id):
    prefix: ClassVar[str] = "gl"


class PlanId(_Id):
    prefix: ClassVar[str] = "pl"


class MemoryId(_Id):
    prefix: ClassVar[str] = "mem"


class ClaimId(_Id):
    prefix: ClassVar[str] = "cl"


class ToolCallId(_Id):
    prefix: ClassVar[str] = "tc"


__all__ = [
    "AgentId",
    "ClaimId",
    "CorrelationId",
    "EventId",
    "ExecutionId",
    "GoalId",
    "MemoryId",
    "PlanId",
    "RequestId",
    "ToolCallId",
    "new_hex",
]