from dataclasses import dataclass,field
@dataclass
class Observation:
    before:dict
    after:dict
    changes:dict=field(default_factory=dict)
    deviation:bool=False
