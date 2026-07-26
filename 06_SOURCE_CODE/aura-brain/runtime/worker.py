"""
AURA Runtime Worker
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Any

logger = logging.getLogger(__name__)


class Worker:
    """Represents a runtime worker."""

    def __init__(self, worker_id: str) -> None:
        self._worker_id = worker_id
        self._busy = False

    @property
    def worker_id(self) -> str:
        return self._worker_id

    @property
    def busy(self) -> bool:
        return self._busy

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute a task."""
        self._busy = True
        try:
            logger.info("Worker %s executing task.", self._worker_id)
            return func(*args, **kwargs)
        finally:
            self._busy = False