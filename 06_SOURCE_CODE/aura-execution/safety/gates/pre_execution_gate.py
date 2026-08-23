class PreExecutionGate:
    def __init__(self,safety_gate): self.safety_gate=safety_gate
    def check(self,action,approved=False): return self.safety_gate.evaluate(action,approved)
