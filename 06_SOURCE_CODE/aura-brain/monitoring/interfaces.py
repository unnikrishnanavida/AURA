"""Interfaces for the monitoring subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MonitoringProtocol(ABC):
    """Common contract for monitoring components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
