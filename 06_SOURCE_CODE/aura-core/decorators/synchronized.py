from __future__ import annotations

from threading import Lock
from functools import wraps

_GLOBAL_LOCK = Lock()


def synchronized(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with _GLOBAL_LOCK:
            return fn(*args, **kwargs)

    return wrapper
