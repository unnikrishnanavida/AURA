from dataclasses import dataclass
@dataclass(frozen=True)
class ToolEvent:
    tool:str
    success:bool
    error:str|None=None
