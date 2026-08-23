class QualityScorer:
    def score(self, success, efficiency, robustness, safety):
        return max(0.0,min(1.0,.35*success+.25*efficiency+.2*robustness+.2*safety))
