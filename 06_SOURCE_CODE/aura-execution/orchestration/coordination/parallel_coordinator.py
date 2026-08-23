from concurrent.futures import ThreadPoolExecutor
class ParallelCoordinator:
    def run(self,functions,max_workers=4):
        with ThreadPoolExecutor(max_workers=max_workers) as pool:return list(pool.map(lambda f:f(),functions))
