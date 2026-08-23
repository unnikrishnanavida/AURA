from dataclasses import dataclass
from typing import Callable
@dataclass
class Tool:
    name:str
    capability:str
    invoke:Callable
    destructive:bool=False
