class OutcomeValidator:
    def validate(self,result): return result.success and result.error is None
