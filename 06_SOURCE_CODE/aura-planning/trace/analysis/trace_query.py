class TraceQuery:
    def by_name(self,record,name): return tuple(e for e in record.events if e.name==name)
    def by_level(self,record,level): return tuple(e for e in record.events if e.level==level)
