"""Interfaces for the meta subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MetaProtocol(ABC):
    """Common contract for meta components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
