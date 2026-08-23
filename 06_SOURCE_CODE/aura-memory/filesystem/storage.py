"""Filesystem storage utilities for AURA Memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, List


class FileSystemStorage:
    """Lightweight JSON-backed filesystem storage."""

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, payload: Dict[str, Any]) -> None:
        if not name:
            raise ValueError("name must be non-empty")
        path = self.base_path / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        if not name:
            raise ValueError("name must be non-empty")
        path = self.base_path / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def delete(self, name: str) -> bool:
        if not name:
            raise ValueError("name must be non-empty")
        path = self.base_path / f"{name}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def exists(self, name: str) -> bool:
        if not name:
            raise ValueError("name must be non-empty")
        return (self.base_path / f"{name}.json").exists()

    def list_names(self) -> List[str]:
        return [path.stem for path in self.base_path.glob("*.json") if path.is_file()]


__all__ = ["FileSystemStorage"]
