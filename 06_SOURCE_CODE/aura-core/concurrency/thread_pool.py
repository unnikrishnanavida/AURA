from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


class ThreadPool:
    def __init__(self, max_workers: int | None = None) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs):
        return self._pool.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)
