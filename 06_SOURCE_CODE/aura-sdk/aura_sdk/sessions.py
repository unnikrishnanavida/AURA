"""Session management.

A session groups related requests under one id, carrying shared context
(identity, metadata). Sessions are bounded to prevent unbounded growth in long
lived clients.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .errors import SdkValidationError


@dataclass
class Session:
    id: str
    identity: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Creates, tracks, and closes sessions up to a configured bound."""

    def __init__(self, *, max_sessions: int = 50) -> None:
        if max_sessions < 1:
            raise SdkValidationError("max_sessions must be >= 1")
        self._max = max_sessions
        self._sessions: dict[str, Session] = {}

    def create(self, *, identity: str, metadata: dict[str, Any] | None = None) -> Session:
        if not identity or not identity.strip():
            raise SdkValidationError("identity must be a non-empty string")
        session = Session(id=f"ses-{len(self._sessions) + 1}", identity=identity, metadata=metadata or {})
        if len(self._sessions) >= self._max:
            oldest = min(self._sessions, key=lambda sid: self._sessions[sid].created_at)
            del self._sessions[oldest]
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def close(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list(self) -> list[Session]:
        return sorted(self._sessions.values(), key=lambda s: s.created_at)

    @property
    def count(self) -> int:
        return len(self._sessions)


__all__ = ["Session", "SessionManager"]