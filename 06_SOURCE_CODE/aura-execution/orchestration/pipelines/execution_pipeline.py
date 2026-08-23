class ExecutionPipeline:
    def __init__(self,steps):self.steps=steps
    def run(self,context):
        for step in self.steps: context=step(context)
        return context
