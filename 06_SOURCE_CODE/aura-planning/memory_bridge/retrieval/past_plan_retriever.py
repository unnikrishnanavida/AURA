class PastPlanRetriever:
    def __init__(self,store,ranker): self.store,self.ranker=store,ranker
    def retrieve(self,goal_key,limit=5): return self.ranker.rank(self.store.search(goal_key),goal_key)[:limit]
