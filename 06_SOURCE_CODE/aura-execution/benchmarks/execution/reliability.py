def reliability(results):return sum(r.success for r in results)/len(results) if results else 0
