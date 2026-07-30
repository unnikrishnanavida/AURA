from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Response:
    status_code: int
    headers: Dict[str, str]
    body: Any | None = None
