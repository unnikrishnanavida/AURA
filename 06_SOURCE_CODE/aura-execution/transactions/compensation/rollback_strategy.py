class RollbackStrategy:
    def rollback(self,tx,manager):manager.compensate(tx.steps);return tx
