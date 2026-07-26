"""Interfaces for the research subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResearchProtocol(ABC):
    """Common contract for research components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
