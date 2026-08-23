class ReplayRunner:
    def __init__(self,executor):self.executor=executor
    def replay(self,request):return self.executor.execute(request)
