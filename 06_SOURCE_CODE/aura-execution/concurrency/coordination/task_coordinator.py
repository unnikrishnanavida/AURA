class TaskCoordinator:
    def __init__(self):self.tasks={}
    def add(self,id,task):self.tasks[id]=task
    def run(self,id):return self.tasks[id]()
