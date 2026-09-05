from ..models.execution_risk import ExecutionRisk


def analyze(action):
    factors=[]
    score=max(0.0,min(1.0,float(action.risk)))
    if action.risk>=.7:factors.append("declared action risk is high")
    if not action.reversible:factors.append("action is irreversible")
    if action.timeout>300:factors.append("long execution window")
    return ExecutionRisk(score,tuple(factors))
