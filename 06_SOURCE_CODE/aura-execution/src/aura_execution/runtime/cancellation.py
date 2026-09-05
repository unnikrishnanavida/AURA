"""Cancellation support for aura-execution.

A :class:`CancellationToken` is checked cooperatively by the execution engine
between steps and inside handlers that choose to support it. Cancellation is
fail-closed: once cancelled, further execution raises :class:`Cancelled`.
"""

from __future__ import annotations

import threading


class Cancelled(Exception):
    """Raised when an execution is cancelled."""


class CancellationToken:
    """A cooperative cancellation signal."""

    def __init__(self) -> None:
        self._cancelled = False
        self._reason: str | None = None
        self._lock = threading.Lock()

    def cancel(self, reason: str = "cancelled by operator") -> None:
        with self._lock:
            self._cancelled = True
            if self._reason is None:
                self._reason = reason

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    @property
    def reason(self) -> str | None:
        with self._lock:
            return self._reason

    def check(self) -> None:
        if self.cancelled:
            raise Cancelled(self.reason or "cancelled")

    def __bool__(self) -> bool:
        return self.cancelled


class CancellationScope:
    """Groups tokens so an operator can cancel an entire plan."""

    def __init__(self) -> None:
        self._tokens: list[CancellationToken] = []

    def child(self) -> CancellationToken:
        token = CancellationToken()
        self._tokens.append(token)
        return token

    def cancel_all(self, reason: str = "cancelled by operator") -> None:
        for token in self._tokens:
            token.cancel(reason)


__all__ = ["CancellationScope", "CancellationToken", "Cancelled"]