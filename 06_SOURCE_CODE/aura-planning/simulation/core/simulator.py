from .event_queue import EventQueue
class Simulator:
    def __init__(self, handlers=None):
        self.handlers=handlers or {}
    def run(self,state,events):
        queue=EventQueue()
        for event in events: queue.push(event)
        history=[]
        while queue:
            event=queue.pop(); state.time=event.time
            handler=self.handlers.get(event.name)
            if handler: handler(state,event)
            history.append(event)
        return state,tuple(history)
