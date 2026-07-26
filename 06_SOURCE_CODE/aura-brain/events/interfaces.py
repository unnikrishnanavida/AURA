"""Interfaces for the events subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EventsProtocol(ABC):
    """Common contract for events components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
