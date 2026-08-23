from .gates.execution_safety_gate import ExecutionSafetyGate
class SafetyEngine:
    def __init__(self): self.gate=ExecutionSafetyGate()
    def evaluate(self,action,approved=False): return self.gate.evaluate(action,approved)
