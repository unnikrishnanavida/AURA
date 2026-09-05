def safe_workspace_path(root,relative):
 p=(root/relative).resolve(); r=root.resolve()
 if r not in p.parents and p!=r: raise PermissionError('workspace escape')
 return p
