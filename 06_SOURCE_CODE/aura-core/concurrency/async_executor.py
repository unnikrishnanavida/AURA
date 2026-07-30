from __future__ import annotations

import asyncio
from typing import Any, Callable


class AsyncExecutor:
    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()

    async def run(self, coro: Callable[..., Any], *args, **kwargs) -> Any:
        return await coro(*args, **kwargs)

    def submit(self, coro: Callable[..., Any], *args, **kwargs):
        return asyncio.ensure_future(coro(*args, **kwargs))
