from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import time


@dataclass
class Span:
    name: str
    start: float = None
    end: float = None
    meta: Dict[str, Any] = None

    def start_span(self):
        self.start = time.time()

    def end_span(self):
        self.end = time.time()
