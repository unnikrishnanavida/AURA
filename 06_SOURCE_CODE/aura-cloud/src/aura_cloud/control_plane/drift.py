def detect_drift(expected,observed):
 return {k:(expected.get(k),observed.get(k)) for k in set(expected)|set(observed) if expected.get(k)!=observed.get(k)}
