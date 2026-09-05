"""Network resilience contract for aura-mobile.

INTERFACE: real implementations use the platform networking stack. The
in-memory client is a deterministic double with explicit reachability control,
so offline behavior can be tested without a device.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NetworkStatus:
    online: bool
    detail: str = ""

    @property
    def is_online(self) -> bool:
        return self.online


class NetworkResilience(abc.ABC):
    """Contract for a resilient network layer."""

    @abc.abstractmethod
    def is_online(self) -> bool: ...

    @abc.abstractmethod
    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...


@dataclass
class InMemoryNetwork(NetworkResilience):
    """Deterministic network double (INTERFACE/SIMULATION: no real I/O)."""

    kind = "memory"
    online: bool = True
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)
    failure: str | None = None

    def is_online(self) -> bool:
        return self.online

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not self.online:
            raise ConnectionError("device is offline")
        if self.failure:
            raise RuntimeError(self.failure)
        return dict(self.responses.get(f"{method} {path}", {"status": "unknown", "path": path}))


__all__ = ["InMemoryNetwork", "NetworkResilience", "NetworkStatus"]