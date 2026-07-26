"""Interfaces for the world subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorldProtocol(ABC):
    """Common contract for world components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
