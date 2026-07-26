"""Interfaces for the kernel subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KernelProtocol(ABC):
    """Common contract for kernel components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
