"""Interfaces for the innovation subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class InnovationProtocol(ABC):
    """Common contract for innovation components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
