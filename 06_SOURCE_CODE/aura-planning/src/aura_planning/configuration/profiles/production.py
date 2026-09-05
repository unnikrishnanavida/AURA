from ..settings import PlanningSettings
def production_settings(): return PlanningSettings(timeout_seconds=30,max_depth=100,search_width=32,metadata={"profile":"production"})
