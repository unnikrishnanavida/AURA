from dataclasses import dataclass,field
@dataclass(slots=True)
class SharedPlan:
    actions:list=field(default_factory=list)
    owners:dict=field(default_factory=dict)
    def assign(self,action,agent): self.actions.append(action); self.owners[getattr(action,"action_id",id(action))]=agent
