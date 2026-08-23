import subprocess
from ..models.tool_output import ToolOutput
class ShellAdapter:
    def __init__(self, allowlist=()): self.allowlist=set(allowlist)
    def invoke(self, command, timeout=30):
        program=command[0] if isinstance(command,(list,tuple)) else str(command).split()[0]
        if program not in self.allowlist:return ToolOutput(False,error="command not allowlisted")
        try:
            p=subprocess.run(command,capture_output=True,text=True,timeout=timeout,shell=False)
            return ToolOutput(p.returncode==0,stdout=p.stdout,stderr=p.stderr,exit_code=p.returncode,error=None if p.returncode==0 else "command failed")
        except subprocess.TimeoutExpired:return ToolOutput(False,error="timeout")
