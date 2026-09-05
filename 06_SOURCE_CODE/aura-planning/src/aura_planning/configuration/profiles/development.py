from ..settings import PlanningSettings
def development_settings(): return PlanningSettings(timeout_seconds=120,max_depth=500,metadata={"profile":"development"})
