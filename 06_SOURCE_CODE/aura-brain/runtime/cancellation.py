"""
AURA Runtime Cancellation
"""

from __future__ import annotations

from threading import Event


class CancellationToken:
    """Represents a cancellation request."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        """Request cancellation."""
        self._event.set()

    def reset(self) -> None:
        """Reset cancellation state."""
        self._event.clear()

    @property
    def is_cancelled(self) -> bool:
        """Returns True if cancellation was requested."""
        return self._event.is_set()