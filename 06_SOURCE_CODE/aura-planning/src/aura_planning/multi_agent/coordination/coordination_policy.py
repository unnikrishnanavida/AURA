from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class CoordinationPolicy:
    mode:str="round_robin"; quorum:int=1
    def validate(self):
        if self.mode not in {"round_robin","auction","consensus"}: raise ValueError("unsupported coordination mode")
        if self.quorum<1: raise ValueError("quorum must be positive")
