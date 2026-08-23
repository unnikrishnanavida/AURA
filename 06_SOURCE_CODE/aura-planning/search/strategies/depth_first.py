class DepthFirst:
    def search(self,start,expand,is_goal,limit=100):
        stack=[(start,())]; seen=set()
        while stack:
            state,path=stack.pop()
            if len(path)>limit: continue
            if is_goal(state): return path
            key=repr(state)
            if key in seen: continue
            seen.add(key)
            stack.extend((ns,path+(a,)) for a,ns in reversed(list(expand(state))))
        return None
