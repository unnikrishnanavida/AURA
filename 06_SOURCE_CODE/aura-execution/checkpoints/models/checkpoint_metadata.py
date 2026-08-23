from dataclasses import dataclass
@dataclass(frozen=True)
class CheckpointMetadata:
    created_at:float
    reason:str
