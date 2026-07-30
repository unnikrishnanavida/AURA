from __future__ import annotations

from functools import wraps


def validates(schema_name: str):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return deco
