class InMemoryExporter:
    def __init__(self): self.items=[]
    def export(self,item): self.items.append(item)
    def drain(self):
        items=tuple(self.items); self.items.clear(); return items
