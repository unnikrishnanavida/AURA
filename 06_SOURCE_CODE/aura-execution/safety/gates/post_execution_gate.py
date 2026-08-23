class PostExecutionGate:
    def check(self,result):
        return bool(result.success) and result.error is None
