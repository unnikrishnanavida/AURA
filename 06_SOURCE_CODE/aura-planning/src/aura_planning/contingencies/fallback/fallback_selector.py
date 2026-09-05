class FallbackSelector:
    def select(self,strategies,trigger):
        return next((s for s in strategies if getattr(s,"trigger",None)==trigger),None)
