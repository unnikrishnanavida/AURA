class MemoryRanker:
    def rank(self,memories,goal_key):
        return tuple(sorted(memories,key=lambda m:(m.goal_key==goal_key,getattr(m,"outcome",0)),reverse=True))
