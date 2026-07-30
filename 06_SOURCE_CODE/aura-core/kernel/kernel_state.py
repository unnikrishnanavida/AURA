from enum import Enum


class KernelState(Enum):
    """Represents the lifecycle state of the Kernel."""

    INITIALIZED = "initialized"
    BOOTING = "booting"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

    def is_active(self) -> bool:
        return self in {KernelState.RUNNING, KernelState.STARTING}
