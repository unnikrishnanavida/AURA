"""Event primitives for aura-memory."""

from typing import Callable, Dict, List, Any


_subscribers: Dict[str, List[Callable[[Any], None]]] = {}


def subscribe(event: str, fn: Callable[[Any], None]) -> None:
	_subscribers.setdefault(event, []).append(fn)


def publish(event: str, payload: Any) -> None:
	for fn in _subscribers.get(event, []):
		try:
			fn(payload)
		except Exception:
			pass


__all__ = ["subscribe", "publish"]
