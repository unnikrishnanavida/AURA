"""Interfaces for the security subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SecurityProtocol(ABC):
    """Common contract for security components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
