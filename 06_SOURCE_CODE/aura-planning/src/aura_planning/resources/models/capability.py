from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class Capability:
    name:str
    level:float=1.0
    def supports(self,required): return self.level>=required
