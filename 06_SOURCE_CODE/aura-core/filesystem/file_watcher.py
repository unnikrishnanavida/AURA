from __future__ import annotations

from typing import Callable


class FileWatcher:
    def __init__(self) -> None:
        self._callbacks: list[Callable] = []

    def watch(self, path: str, callback: Callable) -> None:
        # Placeholder: use watchdog or similar in real implementations
        self._callbacks.append(callback)
