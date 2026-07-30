from __future__ import annotations

import tempfile
from pathlib import Path


class TempManager:
    def __init__(self) -> None:
        self._tempdir = Path(tempfile.mkdtemp(prefix="aura-"))

    @property
    def path(self) -> Path:
        return self._tempdir

    def cleanup(self) -> None:
        try:
            for child in self._tempdir.iterdir():
                if child.is_file():
                    child.unlink()
            self._tempdir.rmdir()
        except Exception:
            pass
