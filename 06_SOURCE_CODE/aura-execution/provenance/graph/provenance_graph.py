class ProvenanceGraph:
    def __init__(self):self.nodes={};self.edges=[]
    def add_node(self,node):self.nodes[node.id]=node
    def link(self,edge):self.edges.append(edge)
    def parents(self,node_id):return [e.source for e in self.edges if e.target==node_id]
