from dataclasses import dataclass
@dataclass(frozen=True)
class CompensatingAction:
    name:str
    handler:object
