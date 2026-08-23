class DeviationDetector:
    def detect(self,expected,observed):
        return {k:(v,observed.get(k)) for k,v in expected.items() if observed.get(k)!=v}
