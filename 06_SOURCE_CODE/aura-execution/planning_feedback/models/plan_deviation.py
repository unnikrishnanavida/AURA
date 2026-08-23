from dataclasses import dataclass
@dataclass(frozen=True)
class PlanDeviation:
    action_id:str
    expected:dict
    observed:dict
