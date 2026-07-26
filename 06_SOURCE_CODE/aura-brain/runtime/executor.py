"""
Runtime Executor
"""

from __future__ import annotations

from .exceptions import WorkerUnavailableError
from .task import Task
from .worker_pool import WorkerPool


class Executor:
    """Executes runtime tasks."""

    def __init__(self, pool: WorkerPool) -> None:
        self._pool = pool

    def execute(self, task: Task, func):
        worker = self._pool.available_worker()

        if worker is None:
            raise WorkerUnavailableError("No available workers.")

        return worker.execute(func, task.payload)
