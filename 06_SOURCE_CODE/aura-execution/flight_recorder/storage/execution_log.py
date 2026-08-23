class ExecutionLog:
    def __init__(self):self.records=[]
    def record(self,record):self.records.append(record)
    def latest(self):return self.records[-1] if self.records else None
