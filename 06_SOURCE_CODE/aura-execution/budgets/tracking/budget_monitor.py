class BudgetMonitor:
    def __init__(self,tracker): self.tracker=tracker
    def remaining(self):
        b=self.tracker.budget
        return {"actions":b.max_actions-self.tracker.actions,"retries":b.max_retries-self.tracker.retries,"time":b.max_time-self.tracker.elapsed,"cost":b.max_cost-self.tracker.cost}
