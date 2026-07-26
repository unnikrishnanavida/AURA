"""
AURA Runtime
"""

from __future__ import annotations
from typing import Callable

from .executor import Executor
from .runtime_events import RuntimeEvent, RuntimeEventType
from .runtime_manager import RuntimeManager
from .task import Task
from .task_queue import TaskQueue
from .worker_pool import WorkerPool


class Runtime:
    """Main runtime interface."""

    def __init__(self, workers: int = 4) -> None:
        self._queue = TaskQueue()
        self._pool = WorkerPool(workers)
        self._executor = Executor(self._pool)
        self._manager = RuntimeManager(self._queue, self._executor, self._pool)

    @property
    def manager(self) -> RuntimeManager:
        return self._manager

    @property
    def queue(self) -> TaskQueue:
        return self._queue

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def worker_pool(self) -> WorkerPool:
        return self._pool

    def start(self) -> None:
        self._manager.start()

    def shutdown(self) -> None:
        self._manager.stop()

    def submit(self, task: Task) -> None:
        self._queue.push(task)
        self._manager._publish_event(RuntimeEventType.TASK_SUBMITTED, {"task_id": task.id})

    def is_running(self) -> bool:
        return self._manager.is_running()

    def on_event(self, callback: Callable[[RuntimeEvent], None]) -> None:
        self._manager.register_listener(callback)
