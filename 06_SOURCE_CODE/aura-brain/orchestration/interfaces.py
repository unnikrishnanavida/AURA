"""Interfaces for the orchestration subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OrchestrationProtocol(ABC):
    """Common contract for orchestration components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
