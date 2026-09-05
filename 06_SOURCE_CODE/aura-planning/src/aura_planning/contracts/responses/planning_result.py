from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class PlanningResult:
    success:bool; plan:object=None; reason:str|None=None; metrics:dict[str,float]=field(default_factory=dict)
    @classmethod
    def failed(cls,reason): return cls(False,None,reason,{})
    @classmethod
    def succeeded(cls,plan,metrics=None): return cls(True,plan,None,metrics or {})
