class SuccessScorer:
    def score(self, result): return 1.0 if bool(result) else 0.0
