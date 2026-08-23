from .lifecycle.sandbox_manager import SandboxManager
class SandboxEngine:
    def __init__(self,policy):self.manager=SandboxManager(policy)
    def acquire(self):return self.manager.create()
