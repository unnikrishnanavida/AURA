class PlanningPipeline:
    def __init__(self,steps=()): self.steps=tuple(steps)
    def run(self,request):
        value=request
        for step in self.steps: value=step(value)
        return value
