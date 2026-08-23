"""Concurrency helpers for aura-memory."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

_executor = ThreadPoolExecutor(max_workers=4)


def run_blocking(fn: Callable[..., Any], *args, **kwargs) -> Any:
    return _executor.submit(fn, *args, **kwargs).result()


__all__ = ["run_blocking"]
