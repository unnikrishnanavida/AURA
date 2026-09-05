import heapq
class BestFirst:
    def search(self,start,expand,is_goal,score):
        counter=0; q=[(score(start),counter,start,())]; seen=set()
        while q:
            _,_,state,path=heapq.heappop(q)
            if is_goal(state): return path
            key=repr(state)
            if key in seen: continue
            seen.add(key)
            for action,next_state in expand(state):
                counter+=1; heapq.heappush(q,(score(next_state),counter,next_state,path+(action,)))
        return None
