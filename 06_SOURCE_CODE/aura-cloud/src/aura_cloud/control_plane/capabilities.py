def require(provider,required):
 missing=set(required)-set(provider.capabilities())
 if missing: raise RuntimeError(f"capability gap: {sorted(missing)}")
