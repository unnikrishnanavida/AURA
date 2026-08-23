AURA Memory working_memory generic module for conversation_buffer.

from __future__ import annotations
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConversationBuffer:
    '''Generic module for working_memory.conversation_buffer.'''

    def health_check(self) -> bool:
        '''Return whether the module is healthy.'''
        return True

    def info(self) -> Dict[str, Any]:
        '''Return runtime module metadata.'''
        return {"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}

    def describe(self) -> Dict[str, str]:
        '''Return a descriptive summary of this module.'''
        return {"package": "working_memory", "module": "conversation_buffer"}


__all__ = ["ConversationBuffer"]
