class ExecutionMetrics:
    def __init__(self):self.count=0;self.successes=0;self.failures=0;self.total_duration=0
    def record(self,success,duration):self.count+=1;self.successes+=int(success);self.failures+=int(not success);self.total_duration+=duration
    @property
    def success_rate(self):return self.successes/self.count if self.count else 0
