class StrategyEvaluator:
    def evaluate(self,strategy,case):
        started=__import__("time").perf_counter(); result=strategy(case); elapsed=__import__("time").perf_counter()-started
        return {"result":result,"latency":elapsed}
