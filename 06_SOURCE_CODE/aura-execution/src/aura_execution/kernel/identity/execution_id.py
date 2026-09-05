"""Execution identity: typed, prefixed execution IDs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionId:
    """A unique execution identifier with a readable ``ex-`` prefix."""

    value: str

    @classmethod
    def new(cls) -> ExecutionId:
        return cls(value=uuid.uuid4().hex[:16])

    def __str__(self) -> str:
        return f"ex-{self.value}"


__all__ = ["ExecutionId"]