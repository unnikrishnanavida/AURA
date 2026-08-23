class ToolRouter:
    def __init__(self,resolver):self.resolver=resolver
    def route(self,capability):
        tools=self.resolver.for_capability(capability)
        return tools[0] if tools else None
