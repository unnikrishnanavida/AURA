AURA Memory edge data model for schemas.

from __future__ import annotations
import dataclasses
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchemasModel:
    '''Schema model for edge.schemas.'''

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default='unnamed')
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SchemasModel":
        return cls(
            id=str(payload.get('id', uuid.uuid4())),
            name=str(payload.get('name', 'unnamed')),
            metadata=dict(payload.get('metadata', {})),
            created_at=float(payload.get('created_at', time.time())),
        )


__all__ = ["SchemasModel"]
