from queue import PriorityQueue

from .task import Task


class TaskQueue:
    """Priority task queue."""

    def __init__(self):
        self._queue = PriorityQueue()

    def push(self, task: Task):
        self._queue.put((task.priority, task))

    def pop(self) -> Task:
        _, task = self._queue.get()
        return task

    def empty(self):
        return self._queue.empty()

    def size(self):
        return self._queue.qsize()