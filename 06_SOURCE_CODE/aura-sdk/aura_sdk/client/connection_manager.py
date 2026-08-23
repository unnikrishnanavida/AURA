"""AURA SDK Client connection_manager.
"""

"""AURA SDK Client connection_manager.

Lightweight connection manager that models open/close semantics for
network-like clients. It provides predictable state transitions for
tests and simple usages.
"""

from typing import Optional


class ConnectionManager:
    """Manager for aura_sdk.client.connection_manager."""

    def __init__(self) -> None:
        self._connected = False
        self._info: Optional[dict] = None

    def open(self, info: dict | None = None) -> None:
        if self._connected:
            raise RuntimeError("connection already open")
        self._connected = True
        self._info = dict(info) if info else {}

    def close(self) -> None:
        if not self._connected:
            raise RuntimeError("connection not open")
        self._connected = False
        self._info = None

    def is_open(self) -> bool:
        return self._connected

    def info(self) -> dict | None:
        return dict(self._info) if self._info is not None else None
