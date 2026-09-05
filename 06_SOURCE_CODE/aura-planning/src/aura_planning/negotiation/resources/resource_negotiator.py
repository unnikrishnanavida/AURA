class ResourceNegotiator:
    def negotiate(self,requests,capacity):
        allocation={}
        remaining=dict(capacity)
        for agent,need in sorted(requests,key=lambda x:sum(x[1].values()),reverse=True):
            if all(remaining.get(k,0)>=v for k,v in need.items()):
                allocation[agent]=dict(need)
                for k,v in need.items(): remaining[k]-=v
        return allocation
