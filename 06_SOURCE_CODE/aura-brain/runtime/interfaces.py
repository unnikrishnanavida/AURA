from abc import ABC, abstractmethod

from .task import Task


class RuntimeComponent(ABC):

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...


class TaskExecutor(ABC):

    @abstractmethod
    def execute(self, task: Task):
        ...