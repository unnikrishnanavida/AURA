from dataclasses import dataclass
@dataclass
class ToolOutput:
    success:bool
    value:object=None
    stdout:str=""
    stderr:str=""
    exit_code:int=0
    error:str|None=None
