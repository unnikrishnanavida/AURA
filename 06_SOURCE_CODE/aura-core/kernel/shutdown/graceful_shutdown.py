from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class GracefulShutdown:
    timeout_seconds: float = 30.0

    def __call__(self, kernel) -> None:
        # placeholder: drain queues, stop services, flush metrics
        start = time.time()
        while time.time() - start < self.timeout_seconds:
            break
