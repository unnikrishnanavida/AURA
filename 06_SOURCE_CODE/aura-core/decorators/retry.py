from __future__ import annotations

import time
from functools import wraps


def retry(attempts: int = 3, delay: float = 0.1):
    def deco(fn):
        @wraps(fn)
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

    return deco
