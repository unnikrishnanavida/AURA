from __future__ import annotations

import logging
from typing import Iterable

from ..kernel import Kernel

logger = logging.getLogger(__name__)


class StartupManager:
    """Executes startup tasks that prepare the runtime (idempotent)."""

    def __init__(self, tasks: Iterable[callable] | None = None) -> None:
        self.tasks = list(tasks or [])

    def add_task(self, task: callable) -> None:
        self.tasks.append(task)

    def run(self, kernel: Kernel) -> None:
        logger.info("StartupManager: running %d tasks", len(self.tasks))
        for t in self.tasks:
            logger.debug("Startup task: %s", getattr(t, "__name__", repr(t)))
            t(kernel)
