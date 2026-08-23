from dataclasses import dataclass,field
from .identity.action_fingerprint import fingerprint
@dataclass
class ActionGenome:
    action_id:str
    version:str="1.0"
    capability_signature:str=""
    preconditions:dict=field(default_factory=dict)
    effects:dict=field(default_factory=dict)
    risk_profile:float=0.
    cost_profile:float=0.
    reliability:float=0.
    execution_history:list=field(default_factory=list)
    failure_patterns:list=field(default_factory=list)
    lineage:object=None
    @classmethod
    def from_action(cls,action):
        return cls(action.action_id,effects=dict(action.effects),preconditions=dict(action.preconditions),capability_signature=action.capability,risk_profile=action.risk,fingerprint=fingerprint(action) if False else "")
