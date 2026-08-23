import time
def measure(executor,request):
    t=time.perf_counter();executor.execute(request);return time.perf_counter()-t
