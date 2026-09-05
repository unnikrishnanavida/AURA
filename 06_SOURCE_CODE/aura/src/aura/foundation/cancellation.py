"""Cooperative cancellation.

Long-running intelligence operations check a :class:`CancellationToken`;
cancellation raises :class:`CancelledError` at the next checkpoint so systems
fail predictably instead of running forever.
"""

from __future__ import annotations

import threading

from aura.foundation.errors import CancelledError


class CancellationToken:
    """Thread-safe cooperative cancellation token."""

    def __init__(self) -> None:
        self._cancelled = False
        self._lock = threading.RLock()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def check(self) -> None:
        if self.cancelled:
            raise CancelledError("operation cancelled")


class CancellationTokenSource:
    """Owns a token; calling :meth:`cancel` cancels the token."""

    def __init__(self) -> None:
        self.token = CancellationToken()
        self._done = False

    def cancel(self) -> None:
        if not self._done:
            self._done = True
            self.token.cancel()


__all__ = ["CancellationToken", "CancellationTokenSource"]