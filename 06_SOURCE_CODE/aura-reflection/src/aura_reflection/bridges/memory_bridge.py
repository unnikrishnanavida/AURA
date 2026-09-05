"""Memory bridge for reflection.

Reflection must NOT automatically write permanent memory. This bridge exposes
an explicit, authorized interface: a lesson is written to a memory store only
when it comes from an approved learning signal and an explicit ``write`` call
is made by a subsystem owner. By default the bridge refuses to write.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from aura_reflection.bridges.learning_bridge import LearningSignal
from aura_reflection.services.reflection_gate import UnauthorizedMutationError


@dataclass(frozen=True)
class MemoryWriteResult:
    ok: bool
    entry_key: str | None = None
    reason: str = ""


class MemoryStore(Protocol):
    """The minimal memory-store contract reflection needs to write lessons."""

    def put(self, key: str, content: dict[str, Any]) -> None: ...


class MemoryBridge:
    """Gated writer of reflected lessons into a memory store."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self._store = store
        self._writes: list[dict[str, Any]] = []

    def write_lesson(
        self,
        signal: LearningSignal,
        *,
        store: MemoryStore | None = None,
    ) -> MemoryWriteResult:
        """Write a lesson to memory ONLY from an approved learning signal.

        The signal must carry a recorded authorizer (proving it passed the
        authorization gate). Reflection never triggers this on its own.
        """
        if not signal.approver:
            raise UnauthorizedMutationError(
                "reflection must not write memory without an approved learning signal"
            )
        target = store or self._store
        if target is None:
            return MemoryWriteResult(ok=False, reason="no memory store configured")
        key = f"reflected_lesson:{signal.signal_id}"
        content = {
            "lesson": signal.lesson,
            "proposed_action": signal.proposed_action,
            "confidence": signal.lesson_confidence,
            "approver": signal.approver,
            "written_at": datetime.now(UTC).isoformat(),
        }
        target.put(key, content)
        self._writes.append({"key": key, **content})
        return MemoryWriteResult(ok=True, entry_key=key)

    @property
    def writes(self) -> list[dict[str, Any]]:
        return list(self._writes)