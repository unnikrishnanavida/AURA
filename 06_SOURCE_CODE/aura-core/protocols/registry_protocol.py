from __future__ import annotations

from typing import Protocol


class RegistryProtocol(Protocol):
    def register(self, name: str, value) -> None: ...

    def get(self, name: str): ...
