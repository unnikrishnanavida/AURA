from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanVersion:
    major:int=1; minor:int=0; patch:int=0
    def bump_patch(self): return PlanVersion(self.major,self.minor,self.patch+1)
    def __str__(self): return f"{self.major}.{self.minor}.{self.patch}"
