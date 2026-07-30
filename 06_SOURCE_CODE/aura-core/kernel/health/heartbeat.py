from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Heartbeat:
    interval_seconds: float = 5.0
    last: float = 0.0

    def tick(self) -> None:
        self.last = time.time()
