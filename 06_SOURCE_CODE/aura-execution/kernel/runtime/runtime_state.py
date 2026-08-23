from dataclasses import dataclass
@dataclass
class RuntimeState:
    running:bool=False
    active_executions:int=0
