from aura_execution.orchestration.orchestrator import Orchestrator
def create_application(orchestrator=None):return orchestrator or Orchestrator.default()
if __name__=="__main__": print("AURA Execution application module loaded")
