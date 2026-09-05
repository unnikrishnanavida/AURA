from ..models.planning_state import PlanningState
def equivalent(a:PlanningState,b:PlanningState,keys=None)->bool:
    keys=set(a.values)|set(b.values) if keys is None else set(keys)
    return all(a.values.get(k)==b.values.get(k) for k in keys)
