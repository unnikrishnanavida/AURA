import time
import unittest

from runtime.runtime import Runtime
from runtime.task import Task
from runtime.runtime_events import RuntimeEventType


class RuntimeManagerTests(unittest.TestCase):
    def test_start_and_stop_runtime(self):
        rt = Runtime(workers=2)

        rt.start()

        # push a simple task
        rt.queue.push(Task(name="echo", payload={"v": 1}, priority=1))

        # allow a little time for processing
        time.sleep(0.2)

        # request shutdown
        rt.shutdown()

        # runtime manager should report stopped
        self.assertFalse(rt.manager.is_running())

    def test_runtime_events_are_published(self):
        events = []
        rt = Runtime(workers=2)
        rt.on_event(lambda event: events.append(event))

        rt.start()
        rt.submit(Task(name="echo", payload={"v": 2}, priority=1))
        time.sleep(0.2)
        rt.shutdown()

        event_types = [event.event_type for event in events]

        self.assertIn(RuntimeEventType.STARTED, event_types)
        self.assertIn(RuntimeEventType.TASK_SUBMITTED, event_types)
        self.assertIn(RuntimeEventType.TASK_STARTED, event_types)
        self.assertIn(RuntimeEventType.TASK_COMPLETED, event_types)
        self.assertIn(RuntimeEventType.STOPPED, event_types)


if __name__ == "__main__":
    unittest.main()
