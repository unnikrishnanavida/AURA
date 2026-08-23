from dataclasses import dataclass
@dataclass(frozen=True)
class RecoveryFeedback:
    action_id:str
    strategy:str
    recovered:bool
