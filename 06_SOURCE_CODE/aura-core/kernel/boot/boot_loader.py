from __future__ import annotations

import logging
from typing import Iterable

from ..kernel import Kernel

logger = logging.getLogger(__name__)


class BootLoader:
    """Responsible for running a sequence of boot tasks.

    Implementations should provide `steps` that accept a Kernel and perform
    idempotent initialization work.
    """

    def __init__(self, steps: Iterable[callable] | None = None) -> None:
        self.steps = list(steps or [])

    def add_step(self, step: callable) -> None:
        self.steps.append(step)

    def run(self, kernel: Kernel) -> None:
        logger.info("BootLoader: running %d steps", len(self.steps))
        for step in self.steps:
            logger.debug("Boot step: %s", getattr(step, "__name__", repr(step)))
            step(kernel)
