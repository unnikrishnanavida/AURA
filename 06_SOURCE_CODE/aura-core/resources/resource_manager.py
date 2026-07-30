from pathlib import Path


class ResourceManager:
    def __init__(self, base: str | Path):
        self.base = Path(base)

    def read_text(self, rel_path: str) -> str:
        p = self.base / rel_path
        return p.read_text(encoding="utf-8")
