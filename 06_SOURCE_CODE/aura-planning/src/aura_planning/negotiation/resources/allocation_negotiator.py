class AllocationNegotiator:
    def allocate(self,bids,capacity):
        ordered=sorted(bids,key=lambda b:b[1],reverse=True)
        return ordered[:capacity]
