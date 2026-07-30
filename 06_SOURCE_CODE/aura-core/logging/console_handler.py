from __future__ import annotations

import logging


class ConsoleHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
