from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .config_parser import ConfigParser


class ConfigLoader:
    """Loads a configuration file and parses it.

    Currently supports JSON. Can be extended to support multiple sources.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._parser = ConfigParser()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        text = self.path.read_text(encoding="utf-8")
        data = json.loads(text)
        return self._parser.parse(data)
