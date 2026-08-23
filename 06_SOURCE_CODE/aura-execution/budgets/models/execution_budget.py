from dataclasses import dataclass
@dataclass
class ExecutionBudget:
    max_actions:int=100; max_retries:int=3; max_time:float=300; max_cost:float=100
