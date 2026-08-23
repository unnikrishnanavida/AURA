from ..environments.sandbox import Sandbox
class SandboxManager:
    def __init__(self,policy):self.policy=policy;self.current=None
    def create(self):self.current=Sandbox(self.policy).start();return self.current
