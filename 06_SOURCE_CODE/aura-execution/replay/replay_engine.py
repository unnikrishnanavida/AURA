class ReplayEngine:
    def __init__(self,runner):self.runner=runner
    def replay(self,request):return self.runner.replay(request)
