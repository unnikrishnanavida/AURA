from __future__ import annotations

import threading


class ReadWriteLock:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc, tb):
        self._lock.release()
