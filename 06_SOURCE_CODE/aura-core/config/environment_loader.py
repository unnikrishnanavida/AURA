from __future__ import annotations

import os
from typing import Dict, Any


class EnvironmentLoader:
    """Load configuration from environment variables with an optional prefix."""

    def __init__(self, prefix: str | None = None) -> None:
        self.prefix = prefix or ""

    def load(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in os.environ.items():
            if not self.prefix or k.startswith(self.prefix):
                key = k[len(self.prefix) :] if self.prefix else k
                out[key.lower()] = v
        return out
