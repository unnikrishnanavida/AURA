class EventStore:
    def __init__(self):self._events=[]
    def append(self,event):self._events.append(event)
    def query(self,execution_id):return [e for e in self._events if getattr(e,"execution_id",None)==execution_id]
