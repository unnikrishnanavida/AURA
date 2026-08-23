class HistoricalOutcomes:
    def __init__(self):self.items=[]
    def add(self,outcome):self.items.append(outcome)
    def recent(self,n=10):return self.items[-n:]
