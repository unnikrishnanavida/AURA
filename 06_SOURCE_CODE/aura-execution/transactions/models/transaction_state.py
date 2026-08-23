from enum import Enum
class TransactionState(str,Enum):PREPARED="PREPARED";COMMITTED="COMMITTED";ABORTED="ABORTED"
