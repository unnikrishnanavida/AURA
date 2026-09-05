class StrategyPromotion:
    def promote(self,learner,threshold=.8):
        best=learner.best()
        return best if best and learner.scores[best][0]>=threshold else None
