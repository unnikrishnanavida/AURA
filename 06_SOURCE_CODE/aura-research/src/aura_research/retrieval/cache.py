from time import monotonic
class TTLCache:
    def __init__(self,ttl=60): self.ttl=ttl; self.data={}
    def get(self,k):
        x=self.data.get(k)
        return None if not x or monotonic()-x[0]>self.ttl else x[1]
    def put(self,k,v): self.data[k]=(monotonic(),v)
