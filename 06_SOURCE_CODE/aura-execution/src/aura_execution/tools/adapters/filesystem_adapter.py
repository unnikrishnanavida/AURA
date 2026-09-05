from pathlib import Path


class FilesystemAdapter:
    def __init__(self,root): self.root=Path(root).resolve()
    def _safe(self,path):
        p=(self.root/path).resolve()
        if self.root not in p.parents and p!=self.root: raise PermissionError("path escapes filesystem sandbox")
        return p
    def read(self,path): return self._safe(Path(path)).read_text(encoding="utf-8")
    def write(self,path,data): 
        p=self._safe(Path(path));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data,encoding="utf-8");return p
