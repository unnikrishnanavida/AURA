class PlanComparison:
    def compare(self,left,right):
        a=[getattr(x,"action_id",repr(x)) for x in getattr(left,"actions",left)]
        b=[getattr(x,"action_id",repr(x)) for x in getattr(right,"actions",right)]
        return {"same":a==b,"added":[x for x in b if x not in a],"removed":[x for x in a if x not in b]}
