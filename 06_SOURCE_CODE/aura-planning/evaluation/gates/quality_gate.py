class QualityGate:
    def __init__(self, threshold=.7): self.threshold=threshold
    def passes(self, score): return score>=self.threshold
