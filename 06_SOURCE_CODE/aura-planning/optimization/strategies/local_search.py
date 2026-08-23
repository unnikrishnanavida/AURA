class LocalSearch:
    def optimize(self,start,neighbors,score,iterations=100):
        current=start; current_score=score(current)
        for _ in range(iterations):
            better=max(neighbors(current),key=score,default=current)
            value=score(better)
            if value<=current_score: break
            current,current_score=better,value
        return current
