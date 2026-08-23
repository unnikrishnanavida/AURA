from dataclasses import dataclass
@dataclass(frozen=True)
class SandboxPolicy:
    allow_network:bool=False
    allow_process:bool=False
    root:str="."
