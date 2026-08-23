from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(frozen=True, slots=True)
class ExecutionId:
    value: UUID
    created_at: datetime

    @classmethod
    def create(cls) -> "ExecutionId":
        return cls(uuid4(), datetime.now(timezone.utc))

    @classmethod
    def from_string(cls, value: str, created_at: datetime | None = None) -> "ExecutionId":
        return cls(UUID(value), created_at or datetime.now(timezone.utc))

    def __str__(self) -> str:
        return str(self.value)

    def short(self) -> str:
        return self.value.hex[:12]
