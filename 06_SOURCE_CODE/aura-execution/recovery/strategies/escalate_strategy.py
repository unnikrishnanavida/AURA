class EscalateStrategy:
    def choose(self,failure):return failure.policy or not failure.transient
