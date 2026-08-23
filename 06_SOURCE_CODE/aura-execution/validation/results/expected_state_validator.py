class ExpectedStateValidator:
    def compare(self,expected,observed):
        mismatches={k:(v,observed.get(k)) for k,v in expected.items() if observed.get(k)!=v}
        return not mismatches,mismatches
