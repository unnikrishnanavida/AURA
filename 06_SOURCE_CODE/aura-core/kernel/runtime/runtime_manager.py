from __future__ import annotations

import logging
from typing import Iterable

from ..kernel import Kernel

logger = logging.getLogger(__name__)


class RuntimeManager:
    """Manages runtime concerns such as monitoring and lifecycle hooks."""

    def __init__(self, monitors: Iterable[callable] | None = None) -> None:
        self.monitors = list(monitors or [])

    def add_monitor(self, monitor: callable) -> None:
        self.monitors.append(monitor)

    def start(self, kernel: Kernel) -> None:
        logger.debug("RuntimeManager starting monitors")
        for m in self.monitors:
            m.start(kernel) if hasattr(m, "start") else m(kernel)

    def stop(self, kernel: Kernel) -> None:
        logger.debug("RuntimeManager stopping monitors")
        for m in self.monitors:
            m.stop(kernel) if hasattr(m, "stop") else None
