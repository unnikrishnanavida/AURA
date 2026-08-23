from dataclasses import dataclass
@dataclass
class CostBudget:
    limit:float; spent:float=0
    def consume(self,amount):
        if self.spent+amount>self.limit:return False
        self.spent+=amount;return True
