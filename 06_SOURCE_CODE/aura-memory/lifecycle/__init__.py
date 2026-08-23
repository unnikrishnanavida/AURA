"""Lifecycle helpers for aura-memory."""

_shutdown_hooks = []


def register_shutdown(fn):
	_shutdown_hooks.append(fn)


def shutdown():
	for fn in list(_shutdown_hooks):
		try:
			fn()
		except Exception:
			pass


__all__ = ["register_shutdown", "shutdown"]
