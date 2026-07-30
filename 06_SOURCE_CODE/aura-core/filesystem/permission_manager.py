from __future__ import annotations

from pathlib import Path


class PermissionManager:
    def set_read_only(self, path: str) -> None:
        p = Path(path)
        p.chmod(0o444)
