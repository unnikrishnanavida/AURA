"""Interfaces for the governance subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GovernanceProtocol(ABC):
    """Common contract for governance components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
