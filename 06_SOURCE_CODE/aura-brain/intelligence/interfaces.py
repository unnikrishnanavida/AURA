"""Interfaces for the intelligence subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IntelligenceProtocol(ABC):
    """Common contract for intelligence components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
