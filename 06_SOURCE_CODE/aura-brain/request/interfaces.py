"""Interfaces for the request subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RequestProtocol(ABC):
    """Common contract for request components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
