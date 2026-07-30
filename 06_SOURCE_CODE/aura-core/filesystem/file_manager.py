from __future__ import annotations

from pathlib import Path
from typing import Union


class FileManager:
    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        return Path(path).read_text(encoding=encoding)

    def write_text(self, path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
