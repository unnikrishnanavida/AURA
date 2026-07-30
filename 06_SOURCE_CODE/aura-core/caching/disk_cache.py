from __future__ import annotations

from pathlib import Path
import pickle


class DiskCache:
    def __init__(self, directory: str) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def set(self, key: str, value) -> None:
        p = self.dir / f"{key}.pkl"
        p.write_bytes(pickle.dumps(value))

    def get(self, key: str):
        p = self.dir / f"{key}.pkl"
        if not p.exists():
            return None
        return pickle.loads(p.read_bytes())
