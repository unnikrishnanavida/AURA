from collections import deque
class BreadthFirst:
    def search(self,start,expand,is_goal):
        q=deque([(start,())]); seen=set()
        while q:
            state,path=q.popleft(); key=repr(state)
            if key in seen: continue
            seen.add(key)
            if is_goal(state): return path
            for action,next_state in expand(state): q.append((next_state,path+(action,)))
        return None
