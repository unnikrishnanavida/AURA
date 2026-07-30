from __future__ import annotations

from pathlib import Path


class ResourceLocator:
    def locate(self, name: str, search_paths: list[str]) -> Path | None:
        for p in search_paths:
            candidate = Path(p) / name
            if candidate.exists():
                return candidate
        return None
