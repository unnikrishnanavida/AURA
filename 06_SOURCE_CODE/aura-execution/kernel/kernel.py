from .runtime.execution_runtime import ExecutionRuntime
from .runtime.runtime_state import RuntimeState
from .lifecycle.lifecycle_manager import LifecycleManager
class Kernel:
    def __init__(self):self.runtime=ExecutionRuntime();self.runtime.state=RuntimeState();self.lifecycle=LifecycleManager(self.runtime)
    def start(self):return self.lifecycle.start()
    def stop(self):return self.lifecycle.stop()
