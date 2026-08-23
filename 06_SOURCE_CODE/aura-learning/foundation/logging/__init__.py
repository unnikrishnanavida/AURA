"""
AURA Logging Framework

Enterprise-grade logging infrastructure for the AURA framework.

This package provides:

- Log levels
- Log records
- Log formatting
- Log handlers
- Logger implementation
- Logging manager

Architecture
------------
LoggingManager
        │
        ▼
     Logger
        │
        ▼
   LogRecord
        │
        ▼
  LogFormatter
        │
        ▼
   LogHandler(s)

Example
-------
>>> from aura.foundation.logging import (
...     LoggingManager,
...     ConsoleHandler,
... )
>>>
>>> manager = LoggingManager()
>>> logger = manager.get_logger("Runtime")
>>> logger.add_handler(ConsoleHandler())
>>> logger.info("AURA Runtime Started")
"""

from .formatter import (
    LogFormatter,
    LogLevel,
    LogRecord,
)

from .handlers import (
    ConsoleHandler,
    FileHandler,
    LogHandler,
    NullHandler,
)

from .logger import Logger

from .manager import LoggingManager

__version__ = "1.0.0"

__author__ = "AURA Framework"

__license__ = "MIT"

__all__ = [
    # Formatter
    "LogLevel",
    "LogRecord",
    "LogFormatter",

    # Handlers
    "LogHandler",
    "ConsoleHandler",
    "FileHandler",
    "NullHandler",

    # Logger
    "Logger",

    # Manager
    "LoggingManager",
]