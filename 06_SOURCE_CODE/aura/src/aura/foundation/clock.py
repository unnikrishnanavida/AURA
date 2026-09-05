"""Clock primitives.

All time-sensitive AURA code depends on the :class:`Clock` protocol so tests
can inject a deterministic clock. No engine calls ``datetime.now()`` directly
for domain decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Provides the current UTC-aware timestamp."""

    def now(self) -> datetime: ...

    def utcnow_iso(self) -> str: ...


class SystemClock:
    """Real wall-clock implementation."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    def utcnow_iso(self) -> str:
        return self.now().isoformat()


class FrozenClock:
    """Clock pinned to a fixed timestamp."""

    def __init__(self, timestamp: datetime | None = None) -> None:
        self._timestamp = (timestamp or datetime(2026, 1, 1, tzinfo=UTC)).replace(
            tzinfo=UTC
        )

    def now(self) -> datetime:
        return self._timestamp

    def utcnow_iso(self) -> str:
        return self._timestamp.isoformat()

    def advance(self, delta: timedelta) -> None:
        self._timestamp = self._timestamp + delta


class ManualClock:
    """Deterministic, manually advanced clock used by tests and simulations."""

    def __init__(self, start: datetime | None = None) -> None:
        self._current = (start or datetime(2026, 1, 1, tzinfo=UTC)).replace(
            tzinfo=UTC
        )

    def now(self) -> datetime:
        return self._current

    def utcnow_iso(self) -> str:
        return self._current.isoformat()

    def advance(self, seconds: float) -> None:
        self._current = self._current + timedelta(seconds=seconds)


__all__ = ["Clock", "FrozenClock", "ManualClock", "SystemClock"]