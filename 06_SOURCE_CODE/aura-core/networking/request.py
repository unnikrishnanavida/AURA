from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Request:
    method: str
    url: str
    headers: Dict[str, str] | None = None
    body: Any | None = None
