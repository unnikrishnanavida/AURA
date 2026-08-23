class ExecutionRuntime:
    def __init__(self):self.state=None
    def attach(self,state):self.state=state
    def close(self):self.state=None
