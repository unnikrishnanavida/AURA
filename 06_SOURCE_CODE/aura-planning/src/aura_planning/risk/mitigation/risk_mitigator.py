class RiskMitigator:
    def choose(self,risk,strategies):
        applicable=[s for s in strategies if getattr(s,"trigger",None)==risk]
        return max(applicable,key=lambda s:s.risk_reduction,default=None)
