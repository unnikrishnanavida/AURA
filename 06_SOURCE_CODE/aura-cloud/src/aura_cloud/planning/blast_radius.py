from dataclasses import dataclass


@dataclass(frozen=True)
class BlastRadius: affected_resources:int; critical_dependencies:int
def risk_score(x): return min(1.0,(x.affected_resources+3*x.critical_dependencies)/100)
