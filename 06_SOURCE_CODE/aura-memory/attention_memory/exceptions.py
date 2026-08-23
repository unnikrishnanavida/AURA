AURA Memory attention_memory exceptions.

from __future__ import annotations
from typing import Any, Dict, Optional


class ExceptionsError(Exception):
    '''Base exception for attention_memory.Exceptions.'''

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {'message': str(self), 'context': self.context}


__all__ = ["ExceptionsError"]
