import logging
class StructuredLogger:
    def __init__(self,name="aura.execution"):self.log=logging.getLogger(name)
    def event(self,name,**data):self.log.info("%s %s",name,data)
