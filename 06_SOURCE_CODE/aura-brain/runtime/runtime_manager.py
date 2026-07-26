"""
Runtime Manager
"""

from __future__ import annotations

from threading import Event, Lock
import signal
import time
from datetime import datetime
from typing import Callable, Optional

from .task_queue import TaskQueue
from .executor import Executor
from .worker_pool import WorkerPool
from .runtime_events import RuntimeEvent, RuntimeEventType
from .runtime_state import RuntimeState
from .scheduler import RuntimeScheduler


class RuntimeManager:
    """Manages runtime lifecycle with graceful startup and shutdown.

    Responsibilities:
    - Ensure components are started in order (scheduler -> workers)
    - Provide a health-check gating mechanism
    - Support graceful shutdown with timeout
    - Expose a cancellation event for cooperative tasks
    """

    def __init__(
        self,
        queue: TaskQueue,
        executor: Executor,
        pool: WorkerPool,
        health_check: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._queue = queue
        self._executor = executor
        self._pool = pool
        self._scheduler = RuntimeScheduler(queue, executor, event_listener=self._publish_event)
        self._state = RuntimeState.CREATED
        self._shutdown_event = Event()
        self._lock = Lock()
        self._health_check = health_check
        self._listeners: list[Callable[[RuntimeEvent], None]] = []

        # Attach signal handlers for graceful startup/shutdown where supported
        try:
            signal.signal(signal.SIGINT, self._on_signal)
            signal.signal(signal.SIGTERM, self._on_signal)
        except Exception:
            # signal handling may not be available in some environments
            pass

    @property
    def state(self) -> RuntimeState:
        return self._state

    def _on_signal(self, signum, frame):
        # called from main thread signal handler
        self.stop()

    def register_listener(self, callback: Callable[[RuntimeEvent], None]) -> None:
        """Register a listener for runtime lifecycle events."""
        self._listeners.append(callback)

    def _publish_event(self, event_type: RuntimeEventType, payload: dict | None = None) -> None:
        event = RuntimeEvent(event_type=event_type, timestamp=datetime.utcnow(), source="runtime_manager", payload=payload)
        for callback in list(self._listeners):
            try:
                callback(event)
            except Exception:
                pass

    def start(self, *, wait_for_healthy: bool = True, timeout: float = 5.0) -> None:
        with self._lock:
            if self._state == RuntimeState.RUNNING:
                return

            self._state = RuntimeState.STARTING

            # Start scheduler
            self._scheduler.start()

            # Optionally wait for health check to pass
            if wait_for_healthy and self._health_check is not None:
                deadline = time.time() + timeout
                while time.time() < deadline:
                    try:
                        if self._health_check():
                            break
                    except Exception:
                        pass
                    time.sleep(0.1)

            self._state = RuntimeState.RUNNING
            self._publish_event(RuntimeEventType.STARTED)

    def stop(self, *, graceful_timeout: float = 5.0) -> None:
        with self._lock:
            if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
                return

            self._state = RuntimeState.STOPPING

            # Stop scheduler from pulling new tasks
            try:
                self._scheduler.stop()
            except Exception:
                pass

            # Wait for queue to drain
            deadline = time.time() + graceful_timeout
            while self._queue.size() > 0 and time.time() < deadline:
                time.sleep(0.05)

            # Signal shutdown to cooperative tasks
            self._shutdown_event.set()

            # Wait briefly for workers to finish current work
            time.sleep(0.1)

            self._state = RuntimeState.STOPPED
            self._publish_event(RuntimeEventType.STOPPED)

    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        return self._shutdown_event.wait(timeout)

    def get_shutdown_event(self) -> Event:
        return self._shutdown_event

    def is_running(self) -> bool:
        return self._state == RuntimeState.RUNNING