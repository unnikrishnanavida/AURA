from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import heapq, time, math

@dataclass(slots=True)
class SearchNode:
    state: object
    parent: "SearchNode|None" = None
    action: object = None
    g: float = 0.0
    h: float = 0.0
    depth: int = 0
    @property
    def f(self): return self.g+self.h
    def path(self):
        result=[]; node=self
        while node and node.action is not None:
            result.append(node.action); node=node.parent
        return tuple(reversed(result))

@dataclass(frozen=True,slots=True)
class SearchLimits:
    max_expansions: int = 10000
    max_depth: int = 100
    timeout_seconds: float = 30.0

@dataclass(frozen=True,slots=True)
class SearchResult:
    success: bool
    node: SearchNode|None
    expansions: int
    generated: int
    duration: float
    reason: str|None = None

class SearchEngine:
    def __init__(self, limits=None):
        self.limits=limits or SearchLimits()

    def _key(self,state):
        values=getattr(state,"values",state)
        try: return tuple(sorted((k,repr(v)) for k,v in values.items()))
        except AttributeError: return repr(state)

    def _successors(self,node,successors):
        for item in successors(node.state):
            if isinstance(item,tuple) and len(item)==2: action,state=item
            else: action,state=None,item
            yield action,state

    def _run(self, frontier, goal, successors, heuristic, cost, mode):
        started=time.perf_counter(); expanded=generated=0; seen={self._key(frontier[0][1].state) if isinstance(frontier,list) else self._key(frontier[0].state)}
        while frontier:
            if time.perf_counter()-started > self.limits.timeout_seconds:
                return SearchResult(False,None,expanded,generated,time.perf_counter()-started,"timeout")
            if expanded >= self.limits.max_expansions:
                return SearchResult(False,None,expanded,generated,time.perf_counter()-started,"expansion_limit")
            node = frontier.pop() if mode=="dfs" else heapq.heappop(frontier)[2] if mode in {"best","astar"} else frontier.popleft()
            if goal(node.state):
                return SearchResult(True,node,expanded,generated,time.perf_counter()-started)
            if node.depth >= self.limits.max_depth:
                continue
            expanded+=1
            for action,state in self._successors(node,successors):
                key=self._key(state)
                if key in seen: continue
                seen.add(key); generated+=1
                step=float(cost(action,state) if cost else getattr(action,"cost",1))
                child=SearchNode(state,node,action,node.g+step,float(heuristic(state) if heuristic else 0),node.depth+1)
                if mode=="dfs": frontier.append(child)
                elif mode=="bfs": frontier.append(child)
                elif mode=="best": heapq.heappush(frontier,(child.h,generated,child))
                else: heapq.heappush(frontier,(child.f,generated,child))
        return SearchResult(False,None,expanded,generated,time.perf_counter()-started,"exhausted")

    def bfs(self,start,goal,successors,cost=None): return self._run(deque([SearchNode(start)]),goal,successors,None,cost,"bfs")
    def dfs(self,start,goal,successors,cost=None): return self._run([SearchNode(start)],goal,successors,None,cost,"dfs")
    def best_first(self,start,goal,successors,heuristic,cost=None):
        return self._run([(float(heuristic(start)),0,SearchNode(start))],goal,successors,heuristic,cost,"best")
    def a_star(self,start,goal,successors,heuristic,cost=None):
        return self._run([(float(heuristic(start)),0,SearchNode(start))],goal,successors,heuristic,cost,"astar")

    def beam_search(self,start,goal,successors,heuristic,beam_width=8):
        frontier=[SearchNode(start)]
        seen={self._key(start)}
        started=time.perf_counter(); expansions=generated=0
        while frontier and expansions<self.limits.max_expansions:
            if time.perf_counter()-started>self.limits.timeout_seconds: break
            candidates=[]
            for node in frontier:
                if goal(node.state):
                    return SearchResult(True,node,expansions,generated,time.perf_counter()-started)
                if node.depth>=self.limits.max_depth: continue
                expansions+=1
                for action,state in self._successors(node,successors):
                    key=self._key(state)
                    if key in seen: continue
                    seen.add(key); generated+=1
                    g=node.g+float(getattr(action,"cost",1))
                    candidates.append(SearchNode(state,node,action,g,float(heuristic(state)),node.depth+1))
            candidates.sort(key=lambda n:n.f)
            frontier=candidates[:beam_width]
        return SearchResult(False,None,expansions,generated,time.perf_counter()-started,"exhausted")
