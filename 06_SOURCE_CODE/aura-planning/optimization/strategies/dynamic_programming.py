class DynamicProgramming:
    def solve(self,items,capacity,value,weight):
        dp=[0]*(capacity+1)
        for item in items:
            w=int(weight(item)); v=value(item)
            for c in range(capacity,w-1,-1): dp[c]=max(dp[c],dp[c-w]+v)
        return dp[capacity]
