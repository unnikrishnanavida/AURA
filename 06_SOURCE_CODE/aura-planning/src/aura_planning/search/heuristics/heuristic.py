from __future__ import annotations
from abc import ABC,abstractmethod
class Heuristic(ABC):
    @abstractmethod
    def estimate(self,state,goal)->float: ...
