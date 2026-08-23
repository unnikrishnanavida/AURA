class ResumeManager:
    def resume(self,checkpoint,state_engine):
        state_engine.state.data.update(checkpoint.state);return state_engine
