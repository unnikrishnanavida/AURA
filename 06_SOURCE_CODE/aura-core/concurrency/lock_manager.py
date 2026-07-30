from __future__ import annotations

import threading


class LockManager:
    def __init__(self) -> None:
        self._locks = {}

    def get_lock(self, name: str) -> threading.Lock:
        if name not in self._locks:
            self._locks[name] = threading.Lock()
        return self._locks[name]
