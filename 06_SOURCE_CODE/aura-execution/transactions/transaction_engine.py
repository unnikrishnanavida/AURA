from .lifecycle.prepare import prepare
from .lifecycle.abort import abort
class TransactionEngine:
    def run(self,tx,work):
        prepare(tx)
        try:return work(tx)
        except Exception:abort(tx);raise
