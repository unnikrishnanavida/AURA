"""Simple environment-backed settings loader."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Settings:
    """Application settings stored in env vars or a JSON config file.

    Only the most common settings are included here; extend as needed.
    """

    app_name: str = field(default_factory=lambda: os.getenv("AURA_APP_NAME", "aura_memory"))
    log_level: str = field(default_factory=lambda: os.getenv("AURA_LOG_LEVEL", "INFO"))
    redis_url: Optional[str] = field(default_factory=lambda: os.getenv("AURA_REDIS_URL"))
    data_dir: str = field(default_factory=lambda: os.getenv("AURA_DATA_DIR", "./data"))

    def as_dict(self) -> Dict[str, Any]:
        return {"app_name": self.app_name, "log_level": self.log_level, "redis_url": self.redis_url, "data_dir": self.data_dir}


def load_settings(path: Optional[str] = None) -> Settings:
    """Load settings from an optional JSON file, then override with env vars."""
    s = Settings()
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for k, v in data.items():
                if hasattr(s, k):
                    setattr(s, k, v)
        except Exception:
            pass
    # env vars already applied via defaults
    return s


__all__ = ["Settings", "load_settings"]
