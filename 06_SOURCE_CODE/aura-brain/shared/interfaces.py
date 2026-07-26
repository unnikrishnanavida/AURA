"""Interfaces for the shared subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SharedProtocol(ABC):
    """Common contract for shared components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
