class DeviationAnalyzer:
    def analyze(self,expected,observed):
        a=getattr(expected,"values",expected); b=getattr(observed,"values",observed)
        keys=set(a)|set(b)
        return {k:(a.get(k),b.get(k)) for k in keys if a.get(k)!=b.get(k)}
