from ..settings import PlanningSettings
def research_settings(): return PlanningSettings(timeout_seconds=300,max_depth=1000,search_width=128,metadata={"profile":"research"})
