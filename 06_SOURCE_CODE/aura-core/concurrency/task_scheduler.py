from __future__ import annotations

import threading
import time
from typing import Callable


class TaskScheduler:
    def __init__(self) -> None:
        self._threads = []

    def schedule(self, delay: float, fn: Callable, *args, **kwargs):
        def _target():
            time.sleep(delay)
            fn(*args, **kwargs)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        self._threads.append(t)
