class EfficiencyScorer:
    def score(self, cost, duration, cost_limit=1.0, duration_limit=1.0):
        return .5*max(0,1-cost/cost_limit)+.5*max(0,1-duration/duration_limit)
