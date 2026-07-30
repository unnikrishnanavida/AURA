from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger(__name__)


class ShutdownManager:
    def __init__(self, steps: Iterable[callable] | None = None) -> None:
        self.steps = list(steps or [])

    def add_step(self, step: callable) -> None:
        self.steps.append(step)

    def run(self, kernel) -> None:
        logger.info("Running shutdown with %d steps", len(self.steps))
        for s in self.steps:
            try:
                s(kernel)
            except Exception:  # pragma: no cover
                logger.exception("Shutdown step failed: %s", getattr(s, "__name__", s))
