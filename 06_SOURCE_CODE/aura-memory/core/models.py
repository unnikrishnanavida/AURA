"""Core base model utilities."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


@dataclass
class BaseModel:
    """Minimal dataclass-based base model with serialization helpers."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str, separators=(",", ":"))

    @classmethod
    def from_dict(cls: Type[T], payload: Dict[str, Any]) -> T:  # type: ignore[override]
        return cls(**payload)  # type: ignore[arg-type]


__all__ = ["BaseModel"]
