from .bootstrap import bootstrap
from .shutdown import shutdown
class LifecycleManager:
    def __init__(self,runtime):self.runtime=runtime
    def start(self):return bootstrap(self.runtime)
    def stop(self):return shutdown(self.runtime)
