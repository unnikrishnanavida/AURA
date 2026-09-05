from .scenarios.scenario_ranker import ScenarioRanker
from .fallback.fallback_selector import FallbackSelector
class ContingencyEngine:
    def __init__(self, recovery=None):
        self.scenarios=ScenarioRanker(); self.fallbacks=FallbackSelector(); self.recovery=recovery
    def rank_scenarios(self, scenarios): return self.scenarios.rank(scenarios)
    def select_fallback(self, candidates, risk_limit=.5): return self.fallbacks.select(candidates,risk_limit)
    def recover(self, failure, context):
        if self.recovery is None: raise RuntimeError("recovery planner unavailable")
        return self.recovery.handle(failure,context)
