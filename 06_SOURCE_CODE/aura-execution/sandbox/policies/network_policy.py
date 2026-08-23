class NetworkPolicy:
    def __init__(self,allowed_hosts=()):self.allowed=set(allowed_hosts)
    def allowed(self,host):return host in self.allowed
