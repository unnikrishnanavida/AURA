def redact(event,sensitive=('token','secret','password')):return {k:('***' if k.lower() in sensitive else v) for k,v in event.items()}
