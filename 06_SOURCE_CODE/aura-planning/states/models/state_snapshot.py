from dataclasses import dataclass
from time import time
@dataclass(frozen=True,slots=True)
class StateSnapshot:
    state_id:str; values:dict; created_at:float
    @classmethod
    def capture(cls,state_id,values): return cls(state_id,dict(values),time())
