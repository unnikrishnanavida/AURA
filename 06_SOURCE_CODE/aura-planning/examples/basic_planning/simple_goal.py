"""Minimal planning example using a state/action model."""
def build_example():
    return {"goal":"clean room","initial_state":{"clean":False}}
if __name__=="__main__": print(build_example())
