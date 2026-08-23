"""AURA SDK Benchmarking benchmark_manager.

Simple benchmarking helpers: measure named timers and durations.
This keeps behaviour predictable for tests and quick diagnostics.
"""

import time
from typing import Dict


class BenchmarkManager:
    """Manager for aura_sdk.benchmarking.benchmark_manager."""

    def __init__(self) -> None:
        self._timers: Dict[str, float] = {}

    def start(self, name: str) -> None:
        if not name:
            raise ValueError("timer name must be non-empty")
        self._timers[name] = time.perf_counter()

    def stop(self, name: str) -> float:
        if name not in self._timers:
            raise KeyError(f"timer not started: {name}")
        elapsed = time.perf_counter() - self._timers.pop(name)
        return elapsed

    def running(self) -> list:
        return list(self._timers.keys())
