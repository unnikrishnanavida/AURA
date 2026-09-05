from abc import ABC, abstractmethod
class RecoveryStrategy(ABC):
    @abstractmethod
    def recover(self, failure, context): ...
