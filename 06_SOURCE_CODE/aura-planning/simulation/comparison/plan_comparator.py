class PlanComparator:
    def compare(self,results):
        return tuple(sorted(results,key=lambda r:(r.get("success",False),-len(r.get("history",()))),reverse=True))
