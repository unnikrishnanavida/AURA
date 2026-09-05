class BeamSearch:
    def search(self,start,expand,is_goal,score,width=5,depth_limit=50):
        frontier=[(start,())]
        for _ in range(depth_limit):
            candidates=[]
            for state,path in frontier:
                if is_goal(state): return path
                candidates.extend((ns,path+(a,)) for a,ns in expand(state))
            candidates.sort(key=lambda x:score(x[0]))
            frontier=candidates[:width]
            if not frontier: break
        return None
