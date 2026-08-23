class CompensationManager:
    def compensate(self,steps):
        for step in reversed(steps):
            if step.compensation:step.compensation()
