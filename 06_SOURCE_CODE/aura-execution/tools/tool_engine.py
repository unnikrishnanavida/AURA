from .models.tool_output import ToolOutput
class ToolEngine:
    def __init__(self,registry): self.registry=registry
    def invoke(self,tool_name,inputs,timeout=30):
        tool=self.registry.resolve(tool_name)
        try:return ToolOutput(True,value=tool.invoke(inputs))
        except Exception as e:return ToolOutput(False,error=str(e))
