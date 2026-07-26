"""
Runtime Scheduler
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable

from .executor import Executor
from .runtime_events import RuntimeEvent, RuntimeEventType
from .task_queue import TaskQueue


class RuntimeScheduler:
    """Consumes tasks from the queue and schedules them onto workers."""

    def __init__(
        self,
        queue: TaskQueue,
        executor: Executor,
        event_listener: Callable[[RuntimeEvent], None] | None = None,
        poll_interval: float = 0.1,
    ) -> None:
        self._queue = queue
        self._executor = executor
        self._event_listener = event_listener
        self._running = False
        self._thread: threading.Thread | None = None
        self._poll_interval = poll_interval

    def _publish_event(self, event_type: RuntimeEventType, payload: dict | None = None) -> None:
        if self._event_listener is None:
            return

        event = RuntimeEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source="runtime_scheduler",
            payload=payload,
        )

        try:
            self._event_listener(event)
        except Exception:
            pass

    def _loop(self) -> None:
        while self._running:
            if self._queue.empty():
                time.sleep(self._poll_interval)
                continue

            task = self._queue.pop()
            self._publish_event(
                RuntimeEventType.TASK_STARTED,
                {"task_id": task.id, "task_name": task.name, "priority": task.priority},
            )

            try:
                result = self._executor.execute(task, lambda payload: payload)
            except Exception as exc:
                self._publish_event(
                    RuntimeEventType.TASK_FAILED,
                    {"task_id": task.id, "task_name": task.name, "error": str(exc)},
                )
                continue

            self._publish_event(
                RuntimeEventType.TASK_COMPLETED,
                {"task_id": task.id, "task_name": task.name, "result": result},
            )

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            try:
                self._thread.join(timeout=timeout)
            except Exception:
                pass
