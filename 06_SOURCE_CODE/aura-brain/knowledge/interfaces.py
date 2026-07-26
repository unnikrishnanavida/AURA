"""Interfaces for the knowledge subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KnowledgeProtocol(ABC):
    """Common contract for knowledge components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
