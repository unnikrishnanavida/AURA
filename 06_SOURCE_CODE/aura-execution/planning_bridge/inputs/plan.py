from dataclasses import dataclass,field
@dataclass
class Plan:
    plan_id:str
    actions:list=field(default_factory=list)
    constraints:list=field(default_factory=list)
