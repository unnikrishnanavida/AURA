Persistence subsystem

This package provides a tiny `Storage` protocol and two reference implementations:

- `InMemoryStorage` — fast in-process store with TTL and an internal janitor thread.
- `FileStorage` — file-backed JSON store for simple durability without external deps.

Usage example:

```py
from aura_memory.persistence import InMemoryStorage
s = InMemoryStorage()
s.set('foo', {'bar': 1})
print(s.get('foo'))
```
