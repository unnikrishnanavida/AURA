class ScenarioRanker:
    def rank(self,scenarios): return tuple(sorted(scenarios,key=lambda s:s.probability,reverse=True))
