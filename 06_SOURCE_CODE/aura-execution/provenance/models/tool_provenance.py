from dataclasses import dataclass
@dataclass(frozen=True)
class ToolProvenance:
    tool:str
    provider:str
