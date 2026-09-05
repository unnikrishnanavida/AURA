class ProvenanceLedger:
    def __init__(self): self.sources={}
    def record(self,source): self.sources[source.source_id]=source
    def get(self,source_id): return self.sources.get(source_id)
