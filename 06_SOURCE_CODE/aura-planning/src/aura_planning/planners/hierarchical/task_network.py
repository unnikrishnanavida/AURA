from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class Task:
    task_id:str
    primitive:bool=False
    action:object=None
    subtasks:tuple=()
@dataclass(frozen=True,slots=True)
class TaskNetwork:
    tasks:tuple
    def primitive_actions(self):
        return tuple(t.action for t in self.tasks if t.primitive and t.action is not None)
