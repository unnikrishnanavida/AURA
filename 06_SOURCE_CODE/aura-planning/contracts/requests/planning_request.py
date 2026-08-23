from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class PlanningRequest:
    goal:object; initial_state:object; available_actions:tuple=(); constraints:tuple=(); options:dict=field(default_factory=dict)
    def validate(self):
        if self.goal is None or self.initial_state is None: raise ValueError("goal and initial state required")
