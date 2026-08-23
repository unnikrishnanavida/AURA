class FilesystemPolicy:
    def __init__(self,root):self.root=root
    def allowed(self,path):return str(path).startswith(str(self.root))
