"""Interfaces for the evolution subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EvolutionProtocol(ABC):
    """Common contract for evolution components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
