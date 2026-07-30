import signal


class Timeout:
    def __init__(self, seconds: float):
        self.seconds = seconds

    def _handler(self, signum, frame):
        raise TimeoutError()

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(int(self.seconds))

    def __exit__(self, exc_type, exc, tb):
        signal.alarm(0)
