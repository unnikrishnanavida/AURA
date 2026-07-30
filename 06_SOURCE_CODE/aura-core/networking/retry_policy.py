from __future__ import annotations

import time
from typing import Callable


def retry(attempts: int = 3, delay: float = 0.5):
    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            last = None
            for _ in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last = exc
                    time.sleep(delay)
            raise last

        return wrapper

    return decorator
