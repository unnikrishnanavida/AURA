AURA Memory providers generic module for graph_provider.

from __future__ import annotations
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class GraphProvider:
    '''Generic module for providers.graph_provider.'''

    def health_check(self) -> bool:
        '''Return whether the module is healthy.'''
        return True

    def info(self) -> Dict[str, Any]:
        '''Return runtime module metadata.'''
        return {"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}

    def describe(self) -> Dict[str, str]:
        '''Return a descriptive summary of this module.'''
        return {"package": "providers", "module": "graph_provider"}


__all__ = ["GraphProvider"]
