class ResourceConflict:
    def find(self,allocations):
        conflicts=[]
        for resource,entries in allocations.items():
            ordered=sorted(entries,key=lambda x:x[0])
            for a,b in zip(ordered,ordered[1:]):
                if a[1]>b[0]: conflicts.append((resource,a,b))
        return conflicts
