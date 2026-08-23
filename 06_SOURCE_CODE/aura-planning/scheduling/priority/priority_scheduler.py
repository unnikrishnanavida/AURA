class PriorityScheduler:
    def order(self,tasks,priorities): return sorted(tasks,key=lambda t:priorities[t].score(),reverse=True)
