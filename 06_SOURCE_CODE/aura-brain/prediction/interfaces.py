"""Interfaces for the prediction subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PredictionProtocol(ABC):
    """Common contract for prediction components."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        raise NotImplementedError
