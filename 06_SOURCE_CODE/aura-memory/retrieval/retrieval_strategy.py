AURA Memory retrieval generic module for retrieval_strategy.

from __future__ import annotations
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RetrievalStrategy:
    '''Generic module for retrieval.retrieval_strategy.'''

    def health_check(self) -> bool:
        '''Return whether the module is healthy.'''
        return True

    def info(self) -> Dict[str, Any]:
        '''Return runtime module metadata.'''
        return {"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}

    def describe(self) -> Dict[str, str]:
        '''Return a descriptive summary of this module.'''
        return {"package": "retrieval", "module": "retrieval_strategy"}


__all__ = ["RetrievalStrategy"]
