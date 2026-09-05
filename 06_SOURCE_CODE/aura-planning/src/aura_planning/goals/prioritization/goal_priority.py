from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class GoalPriority:
    urgency:float; value:float; risk:float=0
    def score(self)->float: return .5*self.urgency+.4*self.value-.1*self.risk
