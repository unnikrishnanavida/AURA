from .models.execution_budget import ExecutionBudget
from .tracking.budget_tracker import BudgetTracker


class BudgetEngine:
    def __init__(self,budget=None): self.tracker=BudgetTracker(budget or ExecutionBudget())
    def check(self): return self.tracker.within_limits()
    def record(self,*args,**kwargs): self.tracker.record(*args,**kwargs)
