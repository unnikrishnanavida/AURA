from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanningCase:
    name:str; request:object; expected_success:bool=True
class PlanningDataset:
    def __init__(self,cases=()): self.cases=tuple(cases)
    def __iter__(self): return iter(self.cases)
