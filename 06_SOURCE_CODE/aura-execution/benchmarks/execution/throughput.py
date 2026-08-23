import time
def benchmark(executor,request,iterations=100):
    t=time.perf_counter()
    for _ in range(iterations):executor.execute(request)
    return iterations/(time.perf_counter()-t)
