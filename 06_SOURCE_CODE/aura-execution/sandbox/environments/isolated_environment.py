from dataclasses import dataclass
@dataclass
class IsolatedEnvironment:
    root:str
    network:bool=False
