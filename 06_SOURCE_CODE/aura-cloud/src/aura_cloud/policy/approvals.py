from dataclasses import dataclass


@dataclass(frozen=True)
class Approval: actor:str; plan_id:str; approved:bool
