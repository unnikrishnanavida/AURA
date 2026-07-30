from __future__ import annotations

from typing import Protocol


class LifecycleProtocol(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...
