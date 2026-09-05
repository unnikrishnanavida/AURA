class SecureStore:
 def __init__(self):self.data={}
 def put(self,k,v):self.data[k]=v
 def get(self,k):return self.data.get(k)
