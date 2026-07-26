"""Interfaces for the bus subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BusProtocol(ABC):
    """Common contract for bus components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
