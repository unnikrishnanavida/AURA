from __future__ import annotations

from typing import Protocol


class ServiceProtocol(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...
