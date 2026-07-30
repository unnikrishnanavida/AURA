from __future__ import annotations

from typing import Protocol, Any


class Serializer(Protocol):
    def dumps(self, obj: Any) -> bytes: ...

    def loads(self, data: bytes) -> Any: ...
