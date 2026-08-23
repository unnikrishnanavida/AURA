"""Messaging primitives: in-memory pub/sub and queue, plus stubs for adapters."""

from __future__ import annotations

import queue
import threading
from typing import Any, Callable, Dict, List


# Simple in-memory pub/sub
_subscribers: Dict[str, List[Callable[[Any], None]]] = {}
_q = queue.Queue()


def publish(topic: str, payload: Any) -> None:
	# push to queue for background workers
	_q.put((topic, payload))
	for fn in list(_subscribers.get(topic, [])):
		try:
			fn(payload)
		except Exception:
			pass


def subscribe(topic: str, fn: Callable[[Any], None]) -> None:
	_subscribers.setdefault(topic, []).append(fn)


def get_queue() -> queue.Queue:
	return _q


# Adapter stubs
class RedisAdapter:
	def __init__(self, url: str):
		raise NotImplementedError("Redis adapter not implemented; replace with real implementation")


__all__ = ["publish", "subscribe", "get_queue", "RedisAdapter"]
