class DeadlineManager:
    def slack(self,start,duration,deadline): return deadline-(start+duration)
    def overdue(self,start,duration,deadline): return self.slack(start,duration,deadline)<0
