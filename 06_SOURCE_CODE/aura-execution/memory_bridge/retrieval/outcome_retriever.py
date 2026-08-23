class OutcomeRetriever:
    def successes(self,executions):return [x for x in executions if x.success]
