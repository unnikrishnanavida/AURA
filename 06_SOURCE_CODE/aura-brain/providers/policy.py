"""Retry, timeout, and circuit-breaker utilities for providers."""

from __future__ import annotations

import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class RetryPolicy:
    retries: int = 3
    backoff_factor: float = 0.2

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        last_exc = None
        for attempt in range(0, max(1, self.retries + 1)):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries:
                    raise
                time.sleep(self.backoff_factor * (2 ** attempt))
        raise last_exc


@dataclass
class TimeoutPolicy:
    timeout_seconds: float = 30.0

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(func, *args, **kwargs)
            try:
                return fut.result(timeout=self.timeout_seconds)
            except FutureTimeout as exc:
                raise TimeoutError("Operation timed out") from exc


class CircuitBreaker:
    """Simple circuit breaker with error threshold and cooldown."""

    def __init__(self, threshold: int = 5, cooldown: float = 60.0):
        self._threshold = threshold
        self._cooldown = cooldown
        self._failures = 0
        self._state = "closed"
        self._lock = threading.Lock()
        self._opened_at: float | None = None

    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        with self._lock:
            if self._state == "open":
                # check cooldown
                if self._opened_at and (time.time() - self._opened_at) > self._cooldown:
                    self._state = "half_open"
                else:
                    raise RuntimeError("Circuit is open")

        try:
            result = func(*args, **kwargs)
        except Exception:
            with self._lock:
                self._failures += 1
                if self._failures >= self._threshold:
                    self._state = "open"
                    self._opened_at = time.time()
            raise
        else:
            with self._lock:
                # on success, reset
                self._failures = 0
                self._state = "closed"
            return result
