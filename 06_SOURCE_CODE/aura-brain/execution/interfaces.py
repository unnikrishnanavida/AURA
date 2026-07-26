"""Interfaces for the execution subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ExecutionProtocol(ABC):
    """Common contract for execution components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
