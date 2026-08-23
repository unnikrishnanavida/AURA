class LearningAdapter:
    def __init__(self,optimizer): self.optimizer=optimizer
    def record_success(self,event): self.optimizer.observe(event.strategy,event.quality)
    def record_failure(self,event): self.optimizer.observe(event.strategy,0.)
