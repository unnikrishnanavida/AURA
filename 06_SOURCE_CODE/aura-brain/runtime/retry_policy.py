"""
Runtime Retry Policy
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


class RetryPolicy:
    """Simple retry policy."""

    def __init__(
        self,
        retries: int = 3,
        delay: float = 1.0,
    ) -> None:
        self._retries = retries
        self._delay = delay

    def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:

        last_error = None

        for _ in range(self._retries):

            try:
                return func(*args, **kwargs)

            except Exception as exc:
                last_error = exc
                time.sleep(self._delay)

        raise last_error