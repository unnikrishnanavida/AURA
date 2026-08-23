class TradeoffAnalyzer:
    def analyze(self, candidates, vectors):
        return sorted(zip(candidates,vectors),key=lambda item:sum(item[1]),reverse=True)
