from __future__ import annotations

from functools import lru_cache


def cached(maxsize: int = 128):
    return lru_cache(maxsize=maxsize)
