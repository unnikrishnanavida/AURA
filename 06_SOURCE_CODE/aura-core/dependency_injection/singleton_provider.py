from __future__ import annotations

from typing import Callable, Any


class SingletonProvider:
    def __init__(self, factory: Callable[..., Any]) -> None:
        self._factory = factory
        self._instance: Any | None = None

    def get(self) -> Any:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance
