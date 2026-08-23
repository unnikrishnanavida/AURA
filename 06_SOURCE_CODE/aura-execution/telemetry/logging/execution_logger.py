class ExecutionLogger:
    def __init__(self,logger):self.logger=logger
    def started(self,eid):self.logger.event("execution.started",execution_id=eid)
    def completed(self,eid,status):self.logger.event("execution.completed",execution_id=eid,status=status)
