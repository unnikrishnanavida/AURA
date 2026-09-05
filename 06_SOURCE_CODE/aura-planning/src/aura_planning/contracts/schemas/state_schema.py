from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class StateSchema:
    state_id:str; values:dict; timestamp:float|None=None
    def validate(self):
        if not self.state_id.strip(): raise ValueError("state id required")
        if any(not str(k).strip() for k in self.values): raise ValueError("empty state key")
