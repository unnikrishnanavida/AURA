from dataclasses import dataclass, field


@dataclass(slots=True)
class ExecutionContext:
    """Execution metadata."""

    task_id: str

    worker_id: str

    metadata: dict = field(default_factory=dict)