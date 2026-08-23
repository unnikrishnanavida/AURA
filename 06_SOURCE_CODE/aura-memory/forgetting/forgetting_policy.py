AURA Memory forgetting generic module for forgetting_policy.

from __future__ import annotations
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ForgettingPolicy:
    '''Generic module for forgetting.forgetting_policy.'''

    def health_check(self) -> bool:
        '''Return whether the module is healthy.'''
        return True

    def info(self) -> Dict[str, Any]:
        '''Return runtime module metadata.'''
        return {"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}

    def describe(self) -> Dict[str, str]:
        '''Return a descriptive summary of this module.'''
        return {"package": "forgetting", "module": "forgetting_policy"}


__all__ = ["ForgettingPolicy"]
