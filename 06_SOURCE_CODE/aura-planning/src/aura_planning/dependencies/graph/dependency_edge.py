from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class DependencyEdge:
    source:str; target:str; lag:float=0.; relation:str="finish_to_start"
    def __post_init__(self):
        if self.source==self.target: raise ValueError("self dependency")
        if self.lag<0: raise ValueError("negative lag")
