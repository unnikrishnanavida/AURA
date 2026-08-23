class ReasoningAdapter:
    def __init__(self,reasoner):self.reasoner=reasoner
    def constraints(self,problem):return self.reasoner.infer_constraints(problem)
