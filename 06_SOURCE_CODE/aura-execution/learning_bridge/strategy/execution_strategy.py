from dataclasses import dataclass
@dataclass
class ExecutionStrategy:
    retries:int=0
    preferred_tool:str|None=None
