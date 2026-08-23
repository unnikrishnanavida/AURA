from dataclasses import dataclass,field
@dataclass
class Transaction:
    id:str
    steps:list=field(default_factory=list)
    completed:list=field(default_factory=list)
