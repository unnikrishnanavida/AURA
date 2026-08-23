from dataclasses import dataclass, field
from typing import Any
@dataclass(frozen=True)
class ActionInput:
    values: dict[str, Any] = field(default_factory=dict)
    def require(self, name): 
        if name not in self.values: raise KeyError(name)
        return self.values[name]
