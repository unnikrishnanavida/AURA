"""Retry policy for the SDK.

Retries are bounded and only attempted for *transient* failures
(timeouts, transport errors). Non-transient failures (validation, 4xx API
errors) fail immediately. Backoff is exponential with deterministic optional
jitter; a callable ``sleep`` is injectable so tests can run without real sleep.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable

from .config import RetryConfig
from .errors import SdkError, SdkRetryExhaustedError


class RetryPolicy:
    """Applies ``RetryConfig`` to an operation that may fail transiently."""

    def __init__(
        self,
        config: RetryConfig | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self.config = config or RetryConfig()
        self._sleep = sleep
        self._rng = rng or random.Random()

    def should_retry(self, error: SdkError) -> bool:
        return error.code in self.config.retryable_codes

    def run(self, operation: Callable[[], object]) -> object:
        """Run ``operation``, retrying transient failures up to max_attempts."""
        last_error: SdkError | None = None
        attempts = 0
        while attempts <= self.config.max_attempts:
            attempts += 1
            try:
                return operation()
            except SdkError as exc:
                last_error = exc
                if not self.should_retry(exc):
                    raise
                if attempts > self.config.max_attempts:
                    break
            self._sleep(self._backoff(attempts))
        if last_error is None:
            raise SdkRetryExhaustedError("retry budget exhausted")
        raise SdkRetryExhaustedError(
            f"request failed after {attempts} attempt(s): {last_error.message}",
            request_id=last_error.request_id,
        ) from last_error

    def _backoff(self, attempt: int) -> float:
        base = self.config.backoff_base_seconds * (2 ** (attempt - 1))
        if self.config.jitter_seconds > 0:
            base += self._rng.uniform(0.0, self.config.jitter_seconds)
        return base


__all__ = ["RetryPolicy"]