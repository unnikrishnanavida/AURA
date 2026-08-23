class LearningAdapter:
    def __init__(self,learner):self.learner=learner
    def feedback(self,stats,success):return self.learner.update(stats,success)
