from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ActionSchema:
    action_id:str; name:str; preconditions:tuple[str,...]=(); effects:tuple[str,...]=(); cost:float=1.; duration:float=0.; capabilities:tuple[str,...]=()
    def validate(self):
        if not self.action_id.strip() or not self.name.strip(): raise ValueError("action identity required")
        if self.cost<0 or self.duration<0: raise ValueError("negative cost/duration")
