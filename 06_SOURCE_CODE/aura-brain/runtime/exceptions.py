class RuntimeError(Exception):
    """Base runtime exception."""


class TaskExecutionError(RuntimeError):
    """Raised when task execution fails."""


class WorkerUnavailableError(RuntimeError):
    """Raised when no worker is available."""


class QueueEmptyError(RuntimeError):
    """Raised when queue is empty."""