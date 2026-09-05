class WorldModelAdapter:
    def __init__(self, reader, writer, synchronizer):
        self.reader,self.writer,self.synchronizer=reader,writer,synchronizer
    def observe(self,query): return self.reader.read(query)
    def update(self,observation): return self.writer.write(observation)
    def planning_state(self,queries): return self.synchronizer.sync(queries)
