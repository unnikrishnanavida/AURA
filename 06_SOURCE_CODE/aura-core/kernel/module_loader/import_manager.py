from __future__ import annotations

import importlib
from typing import Any


class ImportManager:
    """Dynamically import modules and provide a safe wrapper."""

    def import_module(self, name: str) -> Any:
        return importlib.import_module(name)
