from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class ExecutionEvent:
    timestamp:float
    execution_id:str
    event:str
    data:dict
    def as_dict(self):return asdict(self)
