from dataclasses import dataclass
@dataclass
class DispatchResult:
    success:bool
    value:object=None
    error:str|None=None
    attempts:int=1
