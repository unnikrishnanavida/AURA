class OutcomeAnalyzer:
    def analyze(self,result,expected,observed):
        return {"success":result.success,"state_match":all(observed.get(k)==v for k,v in expected.items())}
