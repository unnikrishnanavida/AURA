def validate_dag(nodes):
 r={k:set(v) for k,v in nodes.items()}
 while r:
  ready=[k for k,v in r.items() if not v]
  if not ready:return False
  for k in ready:r.pop(k)
  for deps in r.values():deps.difference_update(ready)
 return True
