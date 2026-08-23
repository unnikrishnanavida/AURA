from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class SimulationResult:
    completed:bool; final_states:tuple=(); observations:tuple=(); metrics:dict[str,float]=field(default_factory=dict); error:str|None=None
