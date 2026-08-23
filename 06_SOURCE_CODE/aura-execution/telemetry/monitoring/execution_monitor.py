class ExecutionMonitor:
    def __init__(self,metrics):self.metrics=metrics
    def snapshot(self):return {"count":self.metrics.count,"success_rate":self.metrics.success_rate}
