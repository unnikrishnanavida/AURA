"""Interfaces for the capabilities subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CapabilitiesProtocol(ABC):
    """Common contract for capabilities components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
