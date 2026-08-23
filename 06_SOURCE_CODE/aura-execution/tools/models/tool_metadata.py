from dataclasses import dataclass
@dataclass(frozen=True)
class ToolMetadata:
    provider:str
    version:str="1"
    timeout_supported:bool=True
