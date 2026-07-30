from __future__ import annotations

from typing import Protocol, Dict, Any


class ConfigSource(Protocol):
    def load(self) -> Dict[str, Any]:
        ...
