from __future__ import annotations

from typing import Callable, Any


class TransientProvider:
    def __init__(self, factory: Callable[..., Any]) -> None:
        self._factory = factory

    def get(self) -> Any:
        return self._factory()
