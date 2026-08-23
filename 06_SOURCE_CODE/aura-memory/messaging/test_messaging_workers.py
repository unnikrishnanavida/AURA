import importlib.util
import os
import sys
import threading
import time

# import messaging module by path
_here = os.path.dirname(__file__)
_path = os.path.join(_here, "__init__.py")
spec = importlib.util.spec_from_file_location("aura_memory.messaging", _path)
messaging = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = messaging
spec.loader.exec_module(messaging)

# import workers module by path
_workers_path = os.path.join(os.path.dirname(_here), "workers", "__init__.py")
workers_spec = importlib.util.spec_from_file_location("aura_memory.workers", _workers_path)
workers = importlib.util.module_from_spec(workers_spec)
assert workers_spec and workers_spec.loader
sys.modules[workers_spec.name] = workers
workers_spec.loader.exec_module(workers)


def test_messaging_workers():
    results = []

    def handler(payload):
        results.append(payload)

    # subscribe handler
    messaging.subscribe("test-topic", handler)
    worker_result = []

    def worker_handler(topic, payload):
        worker_result.append((topic, payload))

    worker = workers.Worker(handler=worker_handler, poll_interval=0.01)
    worker.start()

    messaging.publish("test-topic", {"x": 1})
    time.sleep(0.1)
    assert {"x": 1} in results
    assert ("test-topic", {"x": 1}) in worker_result

    worker.stop()


if __name__ == "__main__":
    test_messaging_workers()
    print("messaging and workers tests passed")
