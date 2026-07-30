from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RuntimeMonitor:
    """Simple runtime monitor with start/stop hooks."""

    name: str = "runtime-monitor"

    def start(self, kernel) -> None:
        logger.debug("Starting monitor %s", self.name)

    def stop(self, kernel) -> None:
        logger.debug("Stopping monitor %s", self.name)
