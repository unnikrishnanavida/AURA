import threading
class LockManager:
    def __init__(self):self._locks={}
    def lock(self,name):self._locks.setdefault(name,threading.Lock());return self._locks[name]
