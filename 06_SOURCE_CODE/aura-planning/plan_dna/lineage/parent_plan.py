from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ParentPlan:
    plan_id:str
    relation:str="derived"
