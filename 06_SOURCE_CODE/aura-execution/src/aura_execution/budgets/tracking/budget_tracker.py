class BudgetTracker:
    def __init__(self,budget): self.budget=budget; self.actions=0; self.retries=0; self.elapsed=0.; self.cost=0.
    def allow_action(self): return self.actions < self.budget.max_actions
    def record(self,duration=0,cost=0,retry=False): self.actions+=1; self.elapsed+=duration; self.cost+=cost; self.retries+=int(retry)
    def within_limits(self): return self.actions<=self.budget.max_actions and self.retries<=self.budget.max_retries and self.elapsed<=self.budget.max_time and self.cost<=self.budget.max_cost
