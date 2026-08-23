import heapq
class AStar:
    def search(self,start,expand,is_goal,heuristic):
        counter=0; q=[(heuristic(start),0,counter,start,())]; best={repr(start):0}
        while q:
            f,g,_,state,path=heapq.heappop(q)
            if is_goal(state): return path
            for action,next_state,cost in expand(state):
                ng=g+cost; key=repr(next_state)
                if ng<best.get(key,float("inf")):
                    best[key]=ng; counter+=1; heapq.heappush(q,(ng+heuristic(next_state),ng,counter,next_state,path+(action,)))
        return None
