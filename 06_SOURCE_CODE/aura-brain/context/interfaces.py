"""Interfaces for the context subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ContextProtocol(ABC):
    """Common contract for context components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
