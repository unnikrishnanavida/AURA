class StrategySelector:
    def select(self,strategies,context):
        ranked=[(float(s.score(context)),s) for s in strategies]
        return max(ranked,key=lambda x:x[0])[1] if ranked else None
