from __future__ import annotations

def validated(schema_name: str):
    def deco(fn):
        def wrapper(*args, **kwargs):
            # placeholder for validation
            return fn(*args, **kwargs)

        return wrapper

    return deco
