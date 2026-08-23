from pathlib import Path
def report(root):
    root=Path(root)
    files=list(root.rglob("*.py"))
    return {"python_files":len(files),"directories":sum(p.is_dir() for p in root.rglob("*")),"bytes":sum(p.stat().st_size for p in files)}
if __name__=="__main__": print(report("."))
