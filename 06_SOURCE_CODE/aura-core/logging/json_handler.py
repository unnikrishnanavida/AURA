from __future__ import annotations

import json
import logging


class JsonHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - simple wrapper
        obj = {
            "name": record.name,
            "level": record.levelname,
            "msg": record.getMessage(),
            "time": self.formatTime(record),
        }
        self.stream.write(json.dumps(obj) + "")
