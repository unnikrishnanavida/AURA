class ResourceLock:
    def __init__(self,lock):self.lock=lock
    def __enter__(self):self.lock.acquire();return self
    def __exit__(self,*args):self.lock.release()
