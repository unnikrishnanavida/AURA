from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class StateVariable:
    name: str
    value: Any
    observable: bool = True
    version: int = 0

    def evolve(self, value):
        return StateVariable(self.name, value, self.observable, self.version + 1)
