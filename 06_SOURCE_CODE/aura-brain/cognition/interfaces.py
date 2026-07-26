"""Interfaces for the cognition subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CognitionProtocol(ABC):
    """Common contract for cognition components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
