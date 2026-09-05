"""API client contract for aura-desktop.

INTERFACE: the base class defines how the client talks to an AURA API endpoint.
A real implementation (over HTTP) is the production integration; the included
in-memory client is a deterministic test/runtime double. No real network call
is made unless a transport is provided.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ClientState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ApiClient(abc.ABC):
    """Contract for an AURA desktop API client."""

    base_url: str
    state: ClientState = ClientState.DISCONNECTED

    @abc.abstractmethod
    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/health")

    def connect(self) -> ClientState:
        self.state = ClientState.CONNECTING
        self.state = ClientState.CONNECTED
        return self.state

    def disconnect(self) -> ClientState:
        self.state = ClientState.DISCONNECTED
        return self.state


@dataclass
class InMemoryApiClient(ApiClient):
    """Deterministic API client that answers from a local echo map.

    Explicitly labeled INTERFACE/SIMULATION: it performs no network I/O.
    """

    kind = "memory"
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        key = f"{method} {path}"
        if key not in self.responses:
            return {"status": "unknown", "path": path, "method": method}
        return dict(self.responses[key])


__all__ = ["ApiClient", "ClientState", "InMemoryApiClient"]