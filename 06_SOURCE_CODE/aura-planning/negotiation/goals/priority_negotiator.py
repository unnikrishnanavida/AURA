class PriorityNegotiator:
    def negotiate(self,left,right):
        return left if getattr(left,"priority",0)>=getattr(right,"priority",0) else right
