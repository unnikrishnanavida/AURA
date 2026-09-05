class DatabaseAdapter:
    def __init__(self, connection_factory): self.connection_factory=connection_factory
    def execute_read(self, query, params=()):
        if not query.lstrip().lower().startswith("select"): raise PermissionError("read adapter accepts SELECT only")
        with self.connection_factory() as conn:return conn.execute(query,params).fetchall()
