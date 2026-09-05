def require(condition,message='precondition failed'):
 if not condition: raise RuntimeError(message)
