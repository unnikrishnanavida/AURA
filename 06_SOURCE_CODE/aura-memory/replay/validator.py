AURA Memory replay validator for validator.

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ValidatorValidator:
    '''Validator for replay.validator.'''

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def validate(self, data: Any) -> bool:
        '''Validate a payload for replay.validator.'''
        if data is None:
            logger.error("Validation failed because data is None")
            raise ValueError("data cannot be None")
        if self.strict and isinstance(data, str) and not data.strip():
            logger.error("Validation failed because string payload is empty")
            raise ValueError("data may not be empty")
        if self.strict and isinstance(data, dict) and not data:
            logger.warning("Validation received empty dict payload")
        return True

    async def validate_async(self, data: Any) -> bool:
        '''Async validation wrapper.'''
        return self.validate(data)


__all__ = ["ValidatorValidator"]
