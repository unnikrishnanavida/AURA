from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def timer(metrics, name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        metrics.set_gauge(name, elapsed)
