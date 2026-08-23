import heapq
class EventQueue:
    def __init__(self): self._items=[]; self._counter=0
    def push(self,event):
        self._counter+=1; heapq.heappush(self._items,(event.time,self._counter,event))
    def pop(self): return heapq.heappop(self._items)[2] if self._items else None
    def __bool__(self): return bool(self._items)
