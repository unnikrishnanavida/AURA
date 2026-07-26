"""
Runtime Worker Pool
"""

from __future__ import annotations

from .worker import Worker


class WorkerPool:
    """Manages runtime workers."""

    def __init__(self, size: int = 4) -> None:
        self._workers = [
            Worker(f"worker-{i+1}")
            for i in range(size)
        ]

    @property
    def workers(self) -> list[Worker]:
        return self._workers

    def available_worker(self) -> Worker | None:
        for worker in self._workers:
            if not worker.busy:
                return worker
        return None

    def size(self) -> int:
        return len(self._workers)