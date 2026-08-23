"""Background worker helpers for aura-memory.

Simple worker runner that pulls tasks from `messaging.get_queue()` and
processes them using a provided handler function.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from ..messaging import get_queue


class Worker:
    def __init__(self, handler: Callable[[str, object], None], poll_interval: float = 0.1):
        self._handler = handler
        self._poll = float(poll_interval)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        q = get_queue()
        while not self._stop.is_set():
            try:
                topic, payload = q.get(timeout=self._poll)
                try:
                    self._handler(topic, payload)
                except Exception:
                    pass
            except Exception:
                time.sleep(self._poll)

    def stop(self, timeout: float = 1.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)


__all__ = ["Worker"]
