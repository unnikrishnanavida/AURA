"""Rate limiting algorithms for aura-api.

Implements a token-bucket and a sliding-window limiter. Both are pure, thread-
safe for a single process, and deterministic so they can be tested precisely.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Protocol


class RateLimiter(Protocol):
    def allow(self, key: str, *, now: float | None = None) -> bool: ...


@dataclass
class TokenBucket:
    """Token-bucket rate limiter (capacity tokens, refill per second)."""

    capacity: float
    refill_per_second: float
    _tokens: dict[str, float] = field(default_factory=dict)
    _last: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        with self._lock:
            tokens = self._tokens.get(key, self.capacity)
            last = self._last.get(key, now)
            elapsed = max(0.0, now - last)
            tokens = min(self.capacity, tokens + elapsed * self.refill_per_second)
            if tokens >= 1.0:
                self._tokens[key] = tokens - 1.0
                self._last[key] = now
                return True
            self._tokens[key] = tokens
            self._last[key] = now
            return False


@dataclass
class SlidingWindow:
    """Sliding-window counter rate limiter."""

    max_requests: int
    window_seconds: float
    _events: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        with self._lock:
            events = [t for t in self._events.get(key, []) if now - t < self.window_seconds]
            if len(events) >= self.max_requests:
                self._events[key] = events
                return False
            events.append(now)
            self._events[key] = events
            return True


@dataclass
class CompositeLimiter:
    """Applies a default limiter per identity with per-route keys."""

    limiter: RateLimiter

    def allow(self, identity: str, route: str, *, now: float | None = None) -> bool:
        return self.limiter.allow(f"{identity}:{route}", now=now)


__all__ = ["CompositeLimiter", "RateLimiter", "SlidingWindow", "TokenBucket"]