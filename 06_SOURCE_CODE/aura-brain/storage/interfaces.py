"""Interfaces for the storage subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageProtocol(ABC):
    """Common contract for storage components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
