from __future__ import annotations

from pathlib import Path


class DirectoryManager:
    def list(self, path: str) -> list[str]:
        p = Path(path)
        return [str(x) for x in p.iterdir()]

    def remove(self, path: str) -> None:
        p = Path(path)
        if p.is_dir():
            for child in p.iterdir():
                if child.is_file():
                    child.unlink()
                else:
                    self.remove(str(child))
            p.rmdir()
