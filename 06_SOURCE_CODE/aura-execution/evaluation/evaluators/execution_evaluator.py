class ExecutionEvaluator:
    def evaluate(self,result):return {"success":result.status.value=="SUCCEEDED"}
