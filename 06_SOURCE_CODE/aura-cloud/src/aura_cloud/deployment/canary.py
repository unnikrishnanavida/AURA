def canary_steps(total): return () if total<=0 else tuple(min(total,x) for x in (1,max(1,total//10),max(1,total//2),total))
