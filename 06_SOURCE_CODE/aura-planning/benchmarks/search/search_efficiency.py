def summarize(search_results):
    if not search_results:return {"mean_expansions":0.0,"mean_seconds":0.0}
    return {
        "mean_expansions":sum(r.expansions for r in search_results)/len(search_results),
        "mean_seconds":sum(r.duration for r in search_results)/len(search_results),
        "success_rate":sum(r.success for r in search_results)/len(search_results),
    }
