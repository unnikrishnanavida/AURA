AURA Memory memory_registry exceptions.

from __future__ import annotations
from typing import Any, Dict, Optional


class ExceptionsError(Exception):
    '''Base exception for memory_registry.Exceptions.'''

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {'message': str(self), 'context': self.context}


__all__ = ["ExceptionsError"]
