class Sandbox:
    def __init__(self,policy):self.policy=policy;self.active=False
    def start(self):self.active=True;return self
    def close(self):self.active=False
