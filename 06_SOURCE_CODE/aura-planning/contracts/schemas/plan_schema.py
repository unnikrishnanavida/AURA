from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanSchema:
    plan_id:str; goal:object; initial_state:object; actions:tuple; total_cost:float; estimated_duration:float
    def validate(self):
        if not self.plan_id.strip() or self.total_cost<0 or self.estimated_duration<0: raise ValueError("invalid plan")
        self.goal.validate(); self.initial_state.validate()
        for action in self.actions: action.validate()
