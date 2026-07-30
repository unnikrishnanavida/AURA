import threading


class Timeout:
    def __init__(self, seconds: float):
        self._seconds = seconds
        self._timer = None

    def __enter__(self):
        self._timer = threading.Timer(self._seconds, lambda: (_ for _ in ()).throw(TimeoutError()))
        self._timer.start()

    def __exit__(self, exc_type, exc, tb):
        if self._timer:
            self._timer.cancel()
