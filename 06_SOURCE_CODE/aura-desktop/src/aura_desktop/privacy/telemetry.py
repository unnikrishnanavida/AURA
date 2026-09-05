def sanitize(event,blocked=('secret','token','password')): return {k:v for k,v in event.items() if k.lower() not in blocked}
