class ConflictCoordinator:
    def resolve(self,plans,score):
        return max(plans,key=score,default=None)
