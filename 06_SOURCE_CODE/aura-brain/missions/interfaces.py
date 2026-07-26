"""Interfaces for the missions subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MissionsProtocol(ABC):
    """Common contract for missions components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
