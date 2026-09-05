def validate(m):
 if not m.channel or not m.correlation_id: raise ValueError('invalid IPC message')
